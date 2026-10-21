---
name: orquestador
description: Coordina el pipeline completo de un sistema de recuperación de información sobre cualquier corpus de textos (descarga → EDA → limpieza → corpus → índices → evaluación → presentación), dejando que cada etapa decida sus parámetros a partir de los datos. Úsala cuando el usuario pida "correr el pipeline", "seguir con la siguiente etapa", "retomar el trabajo" o "ver en qué etapa vamos".
---

# Orquestador del pipeline

Tu único trabajo es **coordinar**. No escribes código de análisis: delegas cada etapa a su skill, haces que se valide y que se respalde. Nunca te saltas una etapa ni avanzas si la anterior no tiene `PASS`.

## Principio: decidir con los datos

Las skills no traen valores fijos de ningún corpus. Cada etapa inspecciona los datos que recibe y decide sus parámetros con las reglas de su sección **"Decide según los datos"** (formato del archivo, columnas, idioma, tamaño, si hay categorías, cuántas consultas, cuántos componentes…).

- `proyecto.yaml`, en la raíz, guarda dos cosas: lo que el usuario fijó y lo que las etapas decidieron. Un valor `auto` (o ausente) significa "decídelo tú con los datos".
- Un valor fijado por el usuario **siempre gana** sobre la regla automática.
- Cada decisión automática se escribe de vuelta en `proyecto.yaml` (reemplazando el `auto`) y se registra en la lista `decisiones` con este formato, para que se pueda auditar:
  ```yaml
  decisiones:
    - {etapa: eda_raw, clave: datos.idioma, valor: es, razon: "98.20% de los documentos tienen más stopwords del español que de cualquier otro idioma"}
  ```
- Ninguna etapa vuelve a decidir algo que ya está en `proyecto.yaml` sin `auto`.

### Cuándo sí preguntar al usuario

Solo en estos casos; en cualquier otro, decide, registra y sigue:

1. No hay forma de obtener los datos (sin URL, sin archivo local) o el archivo no contiene texto.
2. Hay varias columnas candidatas a texto o a categoría y las reglas no dejan una ganadora clara.
3. El corpus mezcla idiomas (ninguno llega a 80% de los documentos).
4. Datos que solo el usuario sabe: nombre del equipo, materia, título del proyecto. Pregúntalos en la etapa que los use (`presentacion`), no antes.

## Etapas (orden fijo)

| # | Etapa | Skill que la ejecuta | Qué decide a partir de los datos | Salida principal |
|---|---|---|---|---|
| 0 | setup | (este orquestador) | — | entorno, `requirements.txt`, `proyecto.yaml` inicial |
| 1 | descarga | `descarga` | formato, codificación, columnas de texto/categoría/título | el CSV en `datos.ruta_raw` |
| 2 | eda_raw | `eda` (modo `raw`) | idioma, símbolos, umbrales de limpieza, modo de evaluación | `reports/eda_raw.md` |
| 3 | limpieza | `limpieza` | modelo de spaCy, stemmer, stopwords extra | `data/processed/corpus_clean.csv` |
| 4 | eda_corpus | `eda` (modo `corpus`) | rangos de Zipf y Heaps, categorías a graficar | `reports/eda_corpus.md` |
| 5 | indices | `indices` | dimensiones de SVD, tópicos de LDA, filtros de frecuencia, consultas de prueba | `models/*`, `src/buscar.py`, `src/ingesta.py` |
| 6 | evaluacion | `evaluacion` | criterio de relevancia, número y tipo de consultas | `reports/metricas.csv` |
| 7 | presentacion | `presentacion` | unidad, nombres y colores de categorías | `presentacion/salida/presentacion_final.pptx` |

## Archivo de estado

`estado/progreso.json` es la única fuente de verdad del avance. Si no existe, créalo así (con `proyecto.nombre`):

```json
{
  "proyecto": "<proyecto.nombre>",
  "etapas": {
    "setup":        {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "descarga":     {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "eda_raw":      {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "limpieza":     {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "eda_corpus":   {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "indices":      {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "evaluacion":   {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""},
    "presentacion": {"estado": "PENDIENTE", "intentos": 0, "commit": null, "fecha": null, "autor": null, "notas": ""}
  }
}
```

Estados válidos: `PENDIENTE`, `EN_CURSO`, `FAIL`, `PASS`, `BLOQUEADA`.

## Ciclo (repite hasta terminar o hasta un BLOQUEADA)

1. `git pull --rebase` para traer el trabajo del equipo. Lee `estado/progreso.json` y `proyecto.yaml`.
2. Elige la **primera** etapa cuyo estado no sea `PASS`.
   - Si está `BLOQUEADA`, detente y muestra al usuario el contenido de `notas`. No continúes.
3. Márcala `EN_CURSO` y guarda el JSON.
4. Ejecuta la skill correspondiente. Si existe el subagente `ejecutor` (modelo Sonnet), delega en él con este mensaje exacto:
   `Ejecuta la skill <nombre> siguiendo su SKILL.md. Lee proyecto.yaml: respeta los valores fijados y decide los que estén en auto con las reglas de "Decide según los datos", escribiéndolos de vuelta con su razón en "decisiones". Si te encuentras en uno de los casos de "Cuándo sí preguntar", detente y repórtalo.`
   Si en `notas` hay un motivo de FAIL previo, añádelo al mensaje como: `Corrección requerida: <notas>`.
5. Ejecuta la skill `validacion-calidad` sobre esa etapa, con un agente distinto al que la ejecutó.
6. Según el resultado:
   - `PASS` → muestra al usuario, en 2 o 3 líneas, las decisiones automáticas nuevas de esa etapa (de la lista `decisiones`) y ejecuta la skill `backup-repo`. Vuelve al paso 2.
   - `FAIL` → la validación ya incrementó `intentos` y escribió `notas`. Si `intentos < 3`, vuelve al paso 3 con la misma etapa. Si `intentos == 3`, marca `BLOQUEADA` y detente.
7. Al terminar todas las etapas, muestra un resumen: etapa, estado, commit corto, y las decisiones automáticas más importantes.

## Etapa 0: setup (la haces tú)

1. **`proyecto.yaml`**: si no existe, cópialo de `skills/orquestador/proyecto_plantilla.yaml` (todo en `auto`) y pide al usuario **solo** dónde están los datos (URL, archivo o carpeta). Lo demás lo decidirán las etapas. Si el usuario da más datos (idioma, columnas, consultas de evaluación), escríbelos: valen más que las reglas.
2. Crea las carpetas: `data/raw`, `data/processed`, `models`, `reports/figuras`, `src`, `estado`, `presentacion/salida`.
3. Crea `requirements.txt` con:
   ```
   pandas>=2.0
   numpy
   scikit-learn>=1.3
   scipy
   rank-bm25
   gensim>=4.3
   spacy>=3.7
   nltk
   matplotlib
   wordcloud
   python-pptx
   pyyaml
   joblib
   openpyxl
   pyarrow
   ```
4. Crea un entorno aislado (conda o venv) con Python `proyecto.python` (si es `auto`, 3.11) y nombre `proyecto.entorno_conda` (si es `auto`, `proyecto.nombre`), e instala `requirements.txt`. El modelo de spaCy **no** se instala aquí: lo instala `limpieza` cuando ya se conoce el idioma. Registra en `ENTORNO.md` las versiones exactas y los pasos para reproducir el entorno en otra computadora.
5. Crea `.gitignore` con: `data/raw/`, `models/*.pkl`, `models/*.npy`, `models/*.model`, `models/*.model.*`, `__pycache__/`, `.ipynb_checkpoints/`, `.venv/`, `.env`, `.DS_Store`, `~$*`.
6. Crea `README.md` con: objetivo, cómo correr el pipeline (`"Ejecuta la skill orquestador"`), tabla de etapas. Complétalo con la descripción del corpus cuando `descarga` y `eda_raw` la conozcan.
7. Llama a `validacion-calidad` para `setup` y continúa el ciclo.

## Subagente recomendado

Si no existe, crea `.claude/agents/ejecutor.md`:

```markdown
---
name: ejecutor
description: Ejecuta una skill de etapa del pipeline de recuperación de información, decidiendo sus parámetros a partir de los datos.
model: sonnet
---
Ejecutas exactamente la skill que te indiquen. Sigues los pasos en orden. Respetas lo fijado en proyecto.yaml y decides lo que esté en auto con las reglas de la skill, registrando cada decisión con su razón. No improvisas fuera de esas reglas. Al terminar, reporta qué archivos creaste, qué decidiste y cualquier advertencia.
```

## Reglas

- Semilla global: `proyecto.semilla` (si es `auto`, 42) en todo lo aleatorio.
- Todo el código va en `src/` como scripts `.py` ejecutables desde la raíz del repo (`python src/xxx.py`). No dejes la lógica solo en notebooks.
- Ningún script escribe a mano valores de `proyecto.yaml`: los lee de ahí.
- Nunca borres salidas de etapas con `PASS` salvo que la validación lo pida.
- Si el usuario pide rehacer una etapa, márcala `PENDIENTE` junto con **todas las posteriores** (dependen de ella). Si cambia un valor de `proyecto.yaml`, rehaz desde la primera etapa que lo usa.

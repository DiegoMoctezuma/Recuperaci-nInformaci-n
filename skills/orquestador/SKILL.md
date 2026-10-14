---
name: orquestador
description: Coordina el pipeline completo de un sistema de recuperación de información sobre un corpus de textos con categoría (descarga → EDA → limpieza → corpus → índices → evaluación → presentación). Úsala cuando el usuario pida "correr el pipeline", "seguir con la siguiente etapa", "retomar el trabajo" o "ver en qué etapa vamos".
---

# Orquestador del pipeline

Tu único trabajo es **coordinar**. No escribes código de análisis: delegas cada etapa a su skill, haces que se valide y que se respalde. Nunca te saltas una etapa ni avanzas si la anterior no tiene `PASS`.

## Configuración del proyecto

Todas las skills son genéricas. Lo que depende del corpus (URL, columnas, idioma, categorías, cifras esperadas, consultas de prueba) vive en **`proyecto.yaml`**, en la raíz del repositorio. Antes de cualquier etapa:

1. Si `proyecto.yaml` no existe, detente y pídeselo al usuario: muéstrale las claves necesarias (secciones `proyecto`, `datos`, `limpieza`, `eda`, `indices`, `evaluacion`, `presentacion`) y no inventes valores. Los conteos esperados (`filas_esperadas`, `categorias`, `duplicados_esperados`) se pueden llenar después de la etapa `eda_raw` si el usuario no los conoce; en ese caso las verificaciones que los usan quedan pendientes hasta entonces.
2. Cuando delegues una etapa, recuerda al ejecutor que lea `proyecto.yaml` y no ponga en el código valores que ya estén ahí.

## Etapas (orden fijo)

| # | Etapa | Skill que la ejecuta | Salida principal |
|---|---|---|---|
| 0 | setup | (este orquestador, ver abajo) | estructura de carpetas, `requirements.txt` |
| 1 | descarga | `descarga` | el CSV en `datos.ruta_raw` |
| 2 | eda_raw | `eda` (modo `raw`) | `reports/eda_raw.md` |
| 3 | limpieza | `limpieza` | `data/processed/corpus_clean.csv` |
| 4 | eda_corpus | `eda` (modo `corpus`) | `reports/eda_corpus.md` (vocabulario, Zipf, Heaps, wordclouds) |
| 5 | indices | `indices` | `models/*.pkl`, `src/buscar.py`, `src/ingesta.py` |
| 6 | evaluacion | `evaluacion` | `reports/metricas.csv` |
| 7 | presentacion | `presentacion` | `presentacion/salida/presentacion_final.pptx` |

## Archivo de estado

`estado/progreso.json` es la única fuente de verdad. Si no existe, créalo así (con `proyecto.nombre` de `proyecto.yaml`):

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

1. `git pull --rebase` para traer el trabajo del equipo. Lee `estado/progreso.json`.
2. Elige la **primera** etapa cuyo estado no sea `PASS`.
   - Si está `BLOQUEADA`, detente y muestra al usuario el contenido de `notas`. No continúes.
3. Márcala `EN_CURSO` y guarda el JSON.
4. Ejecuta la skill correspondiente (tabla de arriba). Si existe el subagente `ejecutor` (modelo Sonnet), delega en él con este mensaje exacto:
   `Ejecuta la skill <nombre> siguiendo su SKILL.md al pie de la letra, con los valores de proyecto.yaml. No tomes decisiones que la skill no indique; si algo falta, detente y repórtalo.`
   Si en `notas` hay un motivo de FAIL previo, añádelo al mensaje como: `Corrección requerida: <notas>`.
5. Ejecuta la skill `validacion-calidad` sobre esa etapa, con un agente distinto al que la ejecutó.
6. Según el resultado:
   - `PASS` → ejecuta la skill `backup-repo` (ella escribe el commit en el JSON). Vuelve al paso 2.
   - `FAIL` → la validación ya incrementó `intentos` y escribió `notas`. Si `intentos < 3`, vuelve al paso 3 con la misma etapa. Si `intentos == 3`, marca `BLOQUEADA` y detente.
7. Al terminar todas las etapas, muestra un resumen: etapa, estado, commit corto.

## Etapa 0: setup (la haces tú)

1. Comprueba que existe `proyecto.yaml` (ver arriba).
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
   ```
4. Crea un entorno aislado (conda o venv) con la versión de Python de `proyecto.python` y el nombre de `proyecto.entorno_conda`, e instala: `pip install -r requirements.txt && python -m spacy download <limpieza.modelo_spacy>`.
   El modelo de spaCy debe ser del idioma del corpus (`datos.idioma`). Registra en `ENTORNO.md` las versiones exactas instaladas y los pasos para reproducir el entorno en otra computadora.
5. Crea `.gitignore` con: `data/raw/`, `models/*.pkl`, `models/*.npy`, `models/*.model`, `models/*.model.*`, `__pycache__/`, `.ipynb_checkpoints/`, `.venv/`, `.env`, `.DS_Store`, `~$*`.
6. Crea `README.md` con: objetivo (a partir de `proyecto.titulo` y `datos.descripcion`), cómo correr el pipeline (`"Ejecuta la skill orquestador"`), tabla de etapas.
7. Llama a `validacion-calidad` para `setup` y continúa el ciclo.

## Subagente recomendado

Si no existe, crea `.claude/agents/ejecutor.md`:

```markdown
---
name: ejecutor
description: Ejecuta una skill de etapa del pipeline de recuperación de información tal cual está escrita.
model: sonnet
---
Ejecutas exactamente la skill que te indiquen. Sigues los pasos en orden, usas las rutas y parámetros indicados y los valores de proyecto.yaml, y no improvisas. Al terminar, reporta qué archivos creaste y cualquier advertencia.
```

## Reglas

- Semilla global: `proyecto.semilla` en todo lo aleatorio.
- Todo el código va en `src/` como scripts `.py` ejecutables desde la raíz del repo (`python src/xxx.py`). No dejes la lógica solo en notebooks.
- Ningún script escribe a mano valores que estén en `proyecto.yaml`: los lee de ahí.
- Nunca borres salidas de etapas con `PASS` salvo que la validación lo pida.
- Si el usuario pide rehacer una etapa, márcala `PENDIENTE` junto con **todas las posteriores** (dependen de ella).

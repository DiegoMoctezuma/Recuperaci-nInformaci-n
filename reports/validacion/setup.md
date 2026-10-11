# Validación de calidad: etapa `setup`

- Fecha: 2026-10-11
- Resultado: **PASS**
- Comando: `conda run -n bbc-ir python src/validar.py --etapa setup` (código de salida 0)
- Entorno: conda `bbc-ir`, Python 3.11.17, pandas 3.0.6
- Detalle máquina: `reports/validacion/setup.json`

## Verificaciones

| id | Descripción | Bloqueante | Resultado | Detalle |
|---|---|---|---|---|
| S1 | requirements.txt existe | sí | PASS | archivo presente |
| S2 | .gitignore existe | sí | PASS | archivo presente |
| S3 | data/raw ignorado por git | sí | PASS | `'data/raw/' in open('.gitignore').read()` es True; `git check-ignore` confirma la regla en `.gitignore:1` |
| S4 | dependencias instaladas | sí | PASS | importa sklearn, rank_bm25, gensim, spacy, wordcloud, pptx y carga `en_core_web_sm` (3.8.0); código de salida 0 |
| S5 | archivo de estado creado | sí | PASS | `estado/progreso.json` existe |

## Revisión cualitativa (contra "Etapa 0: setup" de skills/orquestador/SKILL.md)

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| Carpetas del paso 1 creadas | Sí | existen `data/raw`, `data/processed`, `models`, `reports/figuras`, `src`, `estado`, `presentacion/plantilla`, `presentacion/salida` |
| `requirements.txt` con las 13 dependencias del paso 2 | Sí | las 13 están, con los mismos nombres y mínimos (`pandas>=2.0`, `scikit-learn>=1.3`, `gensim>=4.3`, `spacy>=3.7`); además `ipykernel` y `nbconvert` (desviación acordada) |
| Instalación y modelo spaCy en inglés | Sí | `en_core_web_sm` 3.8.0 carga; no se usó modelo en español; versiones en `requirements-lock.txt` y `ENTORNO.md` |
| `.gitignore` con las 5 entradas del paso 4 | Sí | `data/raw/`, `models/*.pkl`, `__pycache__/`, `.ipynb_checkpoints/`, `.venv/` presentes; extras acordados: `models/*.npy`, `models/*.model`, `models/*.model.*`, `.DS_Store` |
| `README.md` con objetivo, cómo correr el pipeline y tabla de etapas | Sí | incluye las tres secciones y la frase "Ejecuta la skill orquestador" |
| Estado inicial en `estado/progreso.json` | Sí | estructura del orquestador, 8 etapas, `setup` en `EN_CURSO` antes de validar |
| Código en `src/` y ejecutable desde la raíz sin pasos manuales | Sí | `src/validar.py` corre desde la raíz; la etapa no requería más código |
| Reporte `.md` de la etapa | No aplica | la etapa `setup` no define reporte propio; este informe es el de validación |
| Formato (miles con coma, porcentajes con 2 decimales) | Sí | sin cifras de porcentaje; "2,225" con coma en README |

## Contexto: desviaciones acordadas con el usuario (no son motivo de FAIL)

- `requirements.txt` añade `ipykernel` y `nbconvert` para el notebook de entrega.
- `.gitignore` añade `models/*.npy`, `models/*.model` y `.DS_Store`.
- Se usa el entorno conda `bbc-ir` en lugar de un `pip` global.
- No se crea `.claude/agents/ejecutor.md` (el orquestador lo marca como "recomendado", no obligatorio).
- El CSV se movió de la raíz a `data/raw/`.

## Advertencias (menores, no bloquean)

- `README.md` menciona `python src/indices.py` y el notebook `práctica.ipynb`, que aún no existen en `src/`; se crearán en etapas posteriores.
- `data/raw/` está ignorado por git (S3, según la skill), por lo que el CSV no se versiona; la etapa `descarga` debe poder regenerarlo.
- Árbol de git con cambios sin confirmar: `bbc-text.csv` de la raíz aparece borrado (movido a `data/raw/`) y `skills/validacion-calidad/checklist_calidad.yaml` y `skills/presentacion/SKILL.md` aparecen modificados. Verifica que la copia de `./checklist_calidad.yaml` coincide con la que se quiera versionar.
- `src/validar.py` implementa `csv_columnas` como "columnas listadas presentes y en el mismo orden relativo" (se permiten columnas adicionales; se indican en el detalle), según instrucción del solicitante; la skill admite "exactamente/al menos".

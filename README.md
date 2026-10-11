# Recuperación de información sobre BBC News

## Objetivo

Construir y evaluar un sistema de recuperación de información sobre el corpus BBC News
(2,225 noticias en inglés, 5 categorías): limpieza y análisis exploratorio del corpus, índices
CountVectorizer, TF-IDF, BM25 y SVD/LSA (más Word2Vec y LDA como extras), búsqueda por consulta,
evaluación con métricas de ranking y una presentación ejecutiva de resultados.

## Cómo correr el pipeline

1. Prepara el entorno como indica [`ENTORNO.md`](ENTORNO.md) (entorno conda `bbc-ir`, Python 3.11).
2. En Claude Code, desde la raíz del repositorio: **"Ejecuta la skill orquestador"**.
   El orquestador lee `estado/progreso.json` y retoma desde la primera etapa sin `PASS`.

La lógica vive en `src/*.py` (scripts ejecutables desde la raíz con `python src/<script>.py`).
El notebook de entrega `práctica.ipynb` importa esos scripts y muestra las tablas y figuras de `reports/`.

## Etapas

| # | Etapa | Skill | Salida principal |
|---|---|---|---|
| 0 | setup | `orquestador` | estructura de carpetas, `requirements.txt` |
| 1 | descarga | `descarga` | `data/raw/bbc-text.csv` |
| 2 | eda_raw | `eda` (modo `raw`) | `reports/eda_raw.md` |
| 3 | limpieza | `limpieza` | `data/processed/corpus_clean.csv` |
| 4 | eda_corpus | `eda` (modo `corpus`) | `reports/eda_corpus.md` (vocabulario, Zipf, Heaps, wordclouds) |
| 5 | indices | `indices` | `models/*.pkl`, `src/buscar.py`, `src/ingesta.py` |
| 6 | evaluacion | `evaluacion` | `reports/metricas.csv` |
| 7 | presentacion | `presentacion` | `presentacion/salida/presentacion_final.pptx` |

Cada etapa pasa por la skill `validacion-calidad` (contra `checklist_calidad.yaml`) y, con `PASS`,
se respalda con la skill `backup-repo`.

## Carpetas

| Carpeta | Contenido |
|---|---|
| `skills/` | instrucciones de cada etapa |
| `src/` | código del pipeline |
| `data/raw/` | corpus original (no se versiona) |
| `data/processed/` | corpus limpio y consultas de evaluación |
| `models/` | índices (los binarios no se versionan; se regeneran con `python src/indices.py`) |
| `reports/` | reportes, métricas, figuras e informes de validación |
| `presentacion/` | sistema de diseño, guion y presentación final |
| `estado/` | `progreso.json`, estado de cada etapa |

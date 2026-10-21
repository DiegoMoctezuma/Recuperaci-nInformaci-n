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

## Configuración del proyecto

Las skills de `skills/` son genéricas: sirven para cualquier corpus de textos y deciden sus parámetros a
partir de los datos. Cada etapa tiene una sección "Decide según los datos" con reglas: detecta el formato
y las columnas, el idioma (y con él el modelo de spaCy y el stemmer), los umbrales de limpieza, el tamaño
de SVD y LDA, y el criterio de evaluación (juicios de relevancia, categorías o búsqueda de ítem conocido
si no hay categorías).

`proyecto.yaml` guarda lo que el usuario fija y lo que las etapas deciden. En un proyecto nuevo se parte de
`skills/orquestador/proyecto_plantilla.yaml`, donde todo está en `auto` y lo único obligatorio es decir
dónde están los datos. Cada decisión automática queda escrita con su razón en la lista `decisiones`.
El `proyecto.yaml` de este repositorio tiene los valores del corpus BBC fijados a mano.

Para usar el pipeline con otro corpus: copia `skills/`, `src/validar.py` y `checklist_calidad.yaml`,
y pide "Ejecuta la skill orquestador" indicando dónde están los datos.

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

## Video

`video/salida/bbc_news_ir.mp4` cuenta los resultados en 98 segundos como un viaje del héroe: quien busca
una noticia es el héroe y el proyecto es el guía. Todas las cifras en pantalla se leen de `reports/`
al renderizar, y la consulta de la demostración es una real de la evaluación (`auto_023`).

- **Guion**: `video/guion.md`, escrito con la skill `video-storytelling` (audiencia, viaje del héroe y
  triángulo retórico). Queda fuera de las 8 etapas del pipeline y de `checklist_calidad.yaml`.
- **Código**: `src/video/voz.py` genera la narración y `src/video/render.py` dibuja los fotogramas y
  arma el MP4.
- **Requisitos extra**: `ffmpeg` y `edge-tts`, que no están en `requirements.txt`.

```bash
brew install ffmpeg && pip install edge-tts
python src/video/voz.py --voz es-MX-DaliaNeural
python src/video/render.py
```

Los clips de archivo no se versionan; `video/README.md` indica de dónde descargarlos, sus licencias
y cómo cambiar la voz.

## Carpetas

| Carpeta | Contenido |
|---|---|
| `skills/` | instrucciones de cada etapa y del guion del video |
| `src/` | código del pipeline |
| `data/raw/` | corpus original (no se versiona) |
| `data/processed/` | corpus limpio y consultas de evaluación |
| `models/` | índices (los binarios no se versionan; se regeneran con `python src/indices.py`) |
| `reports/` | reportes, métricas, figuras e informes de validación |
| `presentacion/` | sistema de diseño, guion y presentación final |
| `video/` | guion, narración y video final |
| `estado/` | `progreso.json`, estado de cada etapa |

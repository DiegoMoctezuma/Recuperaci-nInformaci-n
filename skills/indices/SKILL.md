---
name: indices
description: Construye los índices de recuperación de un corpus de textos ya limpio (CountVectorizer, TF-IDF, BM25, SVD/LSA, y como extras Word2Vec y LDA), el pipeline de consulta (query → vectorización → similitud coseno o BM25 → ranking) y el pipeline de ingesta de noticias nuevas. Úsala en la etapa indices del pipeline.
---

# Índices, búsqueda e ingesta

Entrada: `data/processed/corpus_clean.csv`, columna `tokens_lemma` (tokens separados por espacio).
Todo usa `random_state=<proyecto.semilla>` (de `proyecto.yaml`). Los modelos se guardan con `joblib` en `models/`.

## Parte A — Construcción de índices (`src/indices.py`)

Para los métodos de sklearn usa `analyzer=str.split` (o `tokenizer=str.split, preprocessor=None, lowercase=False, token_pattern=None`) porque el texto ya está preprocesado.

| Método | Configuración exacta | Archivo |
|---|---|---|
| **CountVectorizer** | `min_df=2, max_df=0.95` | `models/count.pkl` (vectorizador + matriz) |
| **TF-IDF** | `TfidfVectorizer(min_df=2, max_df=0.95, sublinear_tf=True, norm="l2")` | `models/tfidf.pkl` |
| **BM25** | `rank_bm25.BM25Okapi(corpus_tokens, k1=1.5, b=0.75)` con `corpus_tokens = [t.split() for t in tokens_lemma]` | `models/bm25.pkl` |
| **SVD (LSA)** | `TruncatedSVD(n_components=200, random_state=<semilla>)` sobre la matriz TF-IDF, luego `Normalizer(copy=False)` (pipeline `make_pipeline(svd, normalizer)`) | `models/svd.pkl` |
| **Word2Vec** (extra) | `gensim.models.Word2Vec(sentences, vector_size=100, window=5, min_count=2, sg=1, epochs=20, seed=<semilla>, workers=1)`; vector de documento = promedio de los vectores de sus palabras en vocabulario, normalizado L2 | `models/w2v.model`, `models/w2v_docs.npy` |
| **LDA** (extra) | `LatentDirichletAllocation(n_components=10, learning_method="batch", max_iter=20, random_state=<semilla>)` sobre la matriz de CountVectorizer; representación = distribución de tópicos por documento | `models/lda.pkl` |

Además:
1. Para SVD reporta la varianza explicada acumulada y guarda `reports/figuras/svd_varianza.png`.
2. Para LDA guarda las 10 palabras principales de cada tópico en `reports/lda_topicos.csv` y asígnale a cada tópico una etiqueta corta escrita por ti a partir de esas palabras.
3. Guarda `models/doc_index.csv` con `doc_id, category, titulo` en el mismo orden que las filas de las matrices (es el mapeo fila → documento).
4. Escribe `reports/indices.json` con, por método: dimensiones de la matriz (filas × columnas), tamaño del vocabulario, densidad (% de no ceros, 2 decimales) y tiempo de construcción en segundos.

## Parte B — Pipeline de consulta (`src/buscar.py`)

Firma obligatoria:

```python
def buscar(query: str, metodo: str, k: int = 10) -> pandas.DataFrame
# metodo ∈ {"count", "tfidf", "bm25", "svd", "w2v", "lda"}
# columnas: rank, doc_id, category, titulo, score
```

Flujo exacto:
1. `tokens = preprocesar(query, modo="lemma")` (importado de `src/preprocesamiento.py`). Si queda vacío, devuelve un DataFrame vacío y un aviso.
2. Vectoriza la consulta con **el mismo** modelo del índice:
   - count / tfidf: `vectorizador.transform([" ".join(tokens)])`
   - svd: `tfidf.transform(...)` → `pipeline_svd.transform(...)`
   - w2v: promedio de vectores de los tokens en vocabulario (si ninguno está, devuelve vacío con aviso)
   - lda: `lda.transform(count.transform(...))`
3. Puntaje:
   - count, tfidf, svd, w2v, lda → **similitud coseno** (`sklearn.metrics.pairwise.cosine_similarity`) contra la matriz de documentos.
   - bm25 → `bm25.get_scores(tokens)`.
4. Ordena descendente, toma top-k, une con `models/doc_index.csv`, devuelve el ranking.
5. Carga los modelos **una sola vez** (caché a nivel de módulo), no en cada consulta.
6. Agrega un modo CLI: `python src/buscar.py "<consulta>" --metodo bm25 --k 5` que imprima la tabla.

## Parte C — Pipeline de ingesta (`src/ingesta.py`)

Permite agregar documentos nuevos al índice.

```python
def ingestar(textos: list[str], categorias: list[str] | None = None) -> list[str]  # devuelve doc_ids nuevos
```

1. Aplica exactamente el mismo preprocesamiento de `limpieza` (`preprocesar`, `normalizar`).
2. Descarta duplicados exactos contra el corpus existente.
3. Asigna `doc_id` consecutivos a partir del último existente.
4. Añade las filas a `data/processed/corpus_clean.csv` y a `models/doc_index.csv`.
5. **Reconstruye** todos los índices llamando a la función principal de `src/indices.py` (con unos miles de documentos tarda segundos; no intentes actualización incremental).
6. CLI: `python src/ingesta.py --archivo nuevas.csv` (columnas `text` y opcional `category`).

## Parte D — Prueba rápida

Ejecuta las consultas de `indices.consultas_prueba` (en `proyecto.yaml`) con los 6 métodos y guarda los top-5 en `reports/ejemplos_busqueda.md`, indicando para cada una la categoría esperada y cuántos de los 5 resultados la tienen.

La validación usa además `indices.sanidad` (una consulta que debe traer al menos `minimo` documentos de su categoría) y `indices.consulta_rango` (para comprobar 10 resultados y orden descendente): comprueba ambas antes de terminar.

## No hagas

- No reentrenes el vectorizador con la consulta (`fit` solo sobre el corpus; consultas solo `transform`).
- No uses un preprocesamiento distinto en `buscar.py` del que usa el corpus.

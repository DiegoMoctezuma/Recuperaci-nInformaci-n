---
name: indices
description: Construye los índices de recuperación de un corpus de textos ya limpio (CountVectorizer, TF-IDF, BM25, SVD/LSA, y como extras Word2Vec y LDA) ajustando sus parámetros al tamaño del corpus, el pipeline de consulta (query → vectorización → similitud coseno o BM25 → ranking) y el pipeline de ingesta de documentos nuevos. Úsala en la etapa indices del pipeline.
---

# Índices, búsqueda e ingesta

Entrada: `data/processed/corpus_clean.csv`, columna `tokens_lemma` (tokens separados por espacio). Todo lo aleatorio usa `proyecto.semilla`. Los modelos se guardan con `joblib` en `models/`.

Lee la sección `indices` de `proyecto.yaml`. Respeta lo fijado; decide lo que esté en `auto` con las reglas de abajo, escríbelo de vuelta y regístralo en `decisiones` con su razón. Antes de decidir, mide: número de documentos (D), tokens totales (N), mediana de tokens por documento, número de categorías (C, sin contar `sin_categoria`).

## Decide según los datos (si está en `auto`)

| Clave | Regla |
|---|---|
| `min_df` | `2` si D ≥ 200; `1` si es menor (con pocos documentos, filtrar hapax deja vocabulario muy pobre). |
| `max_df` | `0.95`. Si con ese valor quedan menos de 1,000 términos, `1.0`. |
| `svd_componentes` | `min(200, términos − 1, D − 1)`; si D < 1,000, `min(100, términos − 1, D − 1)`. |
| `lda_topicos` | `2 × C` acotado entre 5 y 30; si no hay categorías, `10`. |
| `w2v` | `vector_size=100`, `sg=1`, `workers=1`. `window=5`, o `3` si la mediana es menor de 20 tokens. `min_count=2`, o `1` si N < 50,000. `epochs=20`, o `40` si N < 200,000 (corpus pequeño). |
| `bm25` | `k1=1.5`, `b=0.75`. |
| `consultas_prueba` | Con categorías: 3 consultas de 3 categorías distintas, cada una formada por los 3 términos más característicos de su categoría (de `reports/eda_corpus.md`, términos exclusivos o de mayor frecuencia relativa), con esa categoría como esperada. Sin categorías: los títulos de 3 documentos elegidos al azar, con su `doc_id` como esperado. |
| `sanidad` | La primera de `consultas_prueba`, con `metodo: bm25`, `k: 5` y `minimo: 3` (con categorías) o el `doc_id` esperado (sin categorías). |
| `consulta_rango` | Los 2 términos más frecuentes del corpus unidos por espacio (garantiza al menos 10 resultados). |

Si D > 100,000, avisa en el reporte: la búsqueda exhaustiva por coseno sigue funcionando pero será lenta, y a esa escala convendría un índice invertido para los métodos léxicos y vecinos aproximados para los densos.

## Parte A — Construcción de índices (`src/indices.py`)

Para los métodos de sklearn usa `analyzer=str.split` (o `tokenizer=str.split, preprocessor=None, lowercase=False, token_pattern=None`) porque el texto ya está preprocesado.

| Método | Configuración | Archivo |
|---|---|---|
| **CountVectorizer** | `min_df`, `max_df` decididos | `models/count.pkl` (vectorizador + matriz) |
| **TF-IDF** | `TfidfVectorizer(min_df, max_df, sublinear_tf=True, norm="l2")` | `models/tfidf.pkl` |
| **BM25** | `rank_bm25.BM25Okapi(corpus_tokens, k1, b)` con `corpus_tokens = [t.split() for t in tokens_lemma]` | `models/bm25.pkl` |
| **SVD (LSA)** | `TruncatedSVD(n_components=svd_componentes, random_state=<semilla>)` sobre la matriz TF-IDF, luego `Normalizer(copy=False)` (`make_pipeline(svd, normalizer)`) | `models/svd.pkl` |
| **Word2Vec** (extra) | `gensim.models.Word2Vec(sentences, seed=<semilla>, …parámetros decididos)`; vector de documento = promedio de los vectores de sus palabras en vocabulario, normalizado L2 (vector cero si ninguna está) | `models/w2v.model`, `models/w2v_docs.npy` |
| **LDA** (extra) | `LatentDirichletAllocation(n_components=lda_topicos, learning_method="batch", max_iter=20, random_state=<semilla>)` sobre la matriz de CountVectorizer; representación = distribución de tópicos por documento | `models/lda.pkl` |

Además:
1. Para SVD reporta la varianza explicada acumulada y guarda `reports/figuras/svd_varianza.png`.
2. Para LDA guarda las 10 palabras principales de cada tópico en `reports/lda_topicos.csv` y asígnale a cada tópico una etiqueta corta escrita por ti a partir de esas palabras, en el idioma del corpus o en español.
3. Guarda `models/doc_index.csv` con `doc_id, category, titulo` en el mismo orden que las filas de las matrices (es el mapeo fila → documento).
4. Escribe `reports/indices.json` con, por método: dimensiones de la matriz (filas × columnas), tamaño del vocabulario, densidad (% de no ceros, 2 decimales), tiempo de construcción en segundos y los parámetros usados.

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
4. Ordena descendente, toma top-k, une con `models/doc_index.csv`, devuelve el ranking. `k` puede ser mayor que 10.
5. Carga los modelos **una sola vez** (caché a nivel de módulo) y expón `recargar()` para invalidarla después de una ingesta.
6. Agrega un modo CLI: `python src/buscar.py "<consulta>" --metodo bm25 --k 5` que imprima la tabla.

## Parte C — Pipeline de ingesta (`src/ingesta.py`)

Permite agregar documentos nuevos al índice.

```python
def ingestar(textos: list[str], categorias: list[str] | None = None) -> list[str]  # devuelve doc_ids nuevos
```

1. Aplica exactamente el mismo preprocesamiento de `limpieza` (`preprocesar`, `normalizar`) y las mismas reglas de descarte (vacíos, menos de `min_tokens_documento`).
2. Descarta duplicados exactos contra el corpus existente y dentro del propio lote.
3. Asigna `doc_id` consecutivos a partir del último existente; sin categoría, `sin_categoria`.
4. Añade las filas a `data/processed/corpus_clean.csv` y a `models/doc_index.csv`.
5. **Reconstruye** todos los índices llamando a la función principal de `src/indices.py`. Hasta unas decenas de miles de documentos tarda segundos o pocos minutos; no intentes actualización incremental.
6. CLI: `python src/ingesta.py --archivo nuevos.csv` (columna `text` y opcional `category`).
7. Las funciones aceptan rutas como parámetros (por defecto, las reales) para poder probar la ingesta sobre una copia sin alterar el corpus validado.

## Parte D — Prueba rápida

Ejecuta las consultas de `indices.consultas_prueba` con los 6 métodos y guarda los top-5 en `reports/ejemplos_busqueda.md`, indicando para cada una lo esperado (categoría o `doc_id`) y cuántos de los 5 resultados lo cumplen. Comprueba también `sanidad` y `consulta_rango` antes de terminar, porque la validación los usa.

## No hagas

- No reentrenes el vectorizador con la consulta (`fit` solo sobre el corpus; consultas solo `transform`).
- No uses un preprocesamiento distinto en `buscar.py` del que usa el corpus.
- No cambies un valor de `proyecto.yaml` que el usuario fijó (sin `auto`).

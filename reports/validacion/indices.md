# Validación indices

- Fecha: 2026-10-11
- Resultado: **PASS**
- Comando: `conda run -n bbc-ir python src/validar.py --etapa indices` (código de salida 0)
- SHA-256 de `data/processed/corpus_clean.csv` al inicio y al final: `4920512e71728ad13456b59e46f03f3fdc4f115497cf62ede716c0c688cc9eb0` (coincide). Los MD5 de `models/*`, `reports/*` (salvo `reports/validacion/`) y `data/processed/*` no cambiaron tras las pruebas.

## Verificaciones del checklist

| id | descripción | resultado | detalle |
|---|---|---|---|
| I1 | 4 índices obligatorios | PASS | count, tfidf, bm25, svd .pkl existen |
| I2 | índices extra (W2V, LDA) (no bloqueante) | PASS | w2v.model, w2v_docs.npy, lda.pkl existen |
| I3 | mapeo fila→documento completo | PASS | doc_index.csv = 2,126 filas = corpus_clean.csv |
| I4 | buscar() devuelve 10 resultados en 4 métodos | PASS | código de salida 0 |
| I5 | sanidad: consulta política devuelve política | PASS | código de salida 0 |
| I6 | ranking descendente | PASS | código de salida 0 |
| I7 | pipeline de ingesta | PASS | src/ingesta.py existe |
| I8 | ejemplos de búsqueda | PASS | reports/ejemplos_busqueda.md existe |

## Revisión cualitativa (verificaciones ejecutadas)

| # | Punto | Resultado | Evidencia |
|---|---|---|---|
| 1 | Configuración exacta | sí | `get_params()` de los objetos cargados: CountVectorizer(min_df=2, max_df=0.95, analyzer=str.split, tokenizer/preprocessor None; `lowercase=True` es ignorado con analyzer callable); matriz idéntica a una reconstrucción propia. TfidfVectorizer(min_df=2, max_df=0.95, sublinear_tf=True, norm='l2', analyzer=str.split), mismo vocabulario que count (13,350). BM25Okapi(k1=1.5, b=0.75, epsilon=0.25 por defecto), corpus_size 2,126 y doc_freqs consistentes con `tokens_lemma.split()`. Pipeline (TruncatedSVD(n_components=200, random_state=42), Normalizer(copy=False, l2)); varianza 33.03%. Word2Vec: vector_size=100, window=5, min_count=2, sg=1, epochs=20, seed=42, workers=1 (vocab 14,991). LDA: n_components=10, learning_method='batch', max_iter=20, random_state=42 sobre matriz de count |
| 2 | Coherencia | sí | Matrices con 2,126 filas (count/tfidf 2,126 x 13,350; svd 2,126 x 200; w2v 2,126 x 100; lda 2,126 x 10; bm25 corpus_size 2,126). doc_index.csv: columnas doc_id, category, titulo, orden idéntico a corpus_clean.csv, sin nulos ni doc_id duplicados. indices.json coincide con los objetos: densidad count/tfidf recalculada 0.89% (vocab 13,350); bm25 0.50% (vocab 24,971); svd, w2v, lda 100.00%. Normas L2 de w2v_docs entre 0.9999999 y 1.0000001; filas LDA suman 1.0 |
| 3 | buscar() | sí | Firma `(query: str, metodo: str, k: int = 10) -> DataFrame`; columnas exactas; 6 métodos: 10 filas, rank 1..10, score monótono decreciente, doc_id únicos; k=50 funciona en los 6. Sin `.fit` en buscar.py; usa `preprocesar(..., modo="lemma")`. Caché a nivel de módulo: 1ª consulta 0.006-1.41 s (carga), 2ª 0.0026-0.0118 s. Consulta vacía, solo stopwords, solo dígitos y fuera de vocabulario: DataFrame vacío con columnas correctas y aviso en los 6 métodos, sin excepción; método inválido lanza ValueError. Verificación cruzada con código propio (tokens stock, market, share): top-10 tfidf idéntico en doc_id y score; bm25 `get_scores` idéntico; también count, svd y lda idénticos |
| 4 | CLI | sí | `python src/buscar.py "oil prices rise" --metodo bm25 --k 5` imprime tabla de 5 filas, código 0 |
| 5 | ejemplos_busqueda.md | sí | 3 consultas x 6 métodos x top-5. Categoría esperada 5/5 en las 18 combinaciones (business, politics, tech). 90 filas re-ejecutadas con buscar(): 0 discrepancias (rank, doc_id, category, score a 4 decimales) |
| 6 | LDA y figura | sí | lda_topicos.csv: 10 tópicos, 10 palabras y etiqueta cada uno, idéntico a lo reconstruido. Etiquetas razonables (Música, Cine y premios, Política británica, Tecnología móvil, Fútbol, Empresas/fusiones, Leyes y tribunales). svd_varianza.png: título, ejes y anotación legibles |
| 7 | Ingesta | sí | Firma `ingestar(textos, categorias=None) -> list[str]` (+ rutas opcionales). Prueba sobre copias en el scratchpad: 1 texto nuevo + 1 duplicado exacto -> ids `['doc_2126']`, resumen duplicados=1; corpus 2,127 filas y doc_index 2,127 filas en el mismo orden, primeras 2,126 filas intactas, tokens_lemma = `preprocesar(texto)`, sin categoría -> `desconocida`. Búsqueda "zorblax quantum widget" sobre los modelos temporales: nuevo doc en rank 1 en count, tfidf, bm25, svd y w2v (lda no, es coarse, 10 dimensiones). 2ª ingesta: duplicado, texto corto (<20 tokens) y texto válido -> `['doc_2127']`; longitud de categorías distinta lanza ValueError. No se ejecutó la CLI real |
| 8 | Determinismo | sí | `construir_indices` a directorio temporal (37.8 s): top-10 y scores de 3 consultas x 6 métodos idénticos (diferencia máxima 0.0 en 18/18); doc_index.csv y lda_topicos.csv idénticos; w2v_docs, svd y lda matrices con diferencia máxima 0.0 |

## Advertencias (no bloqueantes)

1. La ingesta descarta también textos con < 20 tokens (misma regla que `limpieza`, `MIN_TOKENS`), además de duplicados exactos. Decisión razonable y coherente con el corpus; no contradice la skill.
2. Noticias sin categoría quedan como `desconocida`. Aceptable, pero la etapa `evaluacion` debe excluirlas del cálculo por categoría.
3. Consulta totalmente fuera de vocabulario devuelve vacío con aviso en todos los métodos (la skill solo lo exige explícitamente para w2v y consulta vacía); extensión coherente.
4. Tras una ingesta las etiquetas LDA se reasignan por solapamiento y pueden degradarse: en la prueba temporal (2,128 docs) 3 de 10 tópicos quedaron como "sin etiqueta (revisar)". Es un límite conocido de LDA (el orden de tópicos cambia al reentrenar); requiere revisión manual de `lda_topicos.csv` tras ingestar.
5. SVD explica 33.03% de la varianza con 200 componentes (cifra correcta y documentada en indices.json y la figura; sin umbral en la skill).
6. Etiqueta del tópico 4 "Rugby y fútbol: partidos" es algo ambigua (palabras ball, try, penalty, ireland, italy apuntan sobre todo a rugby); el tópico 5 está marcado honestamente como mixto.
7. En `svd_varianza.png` el texto de la anotación se cruza con la curva cerca de los 175 componentes (legible, defecto estético menor).
8. Durante la reconstrucción de Word2Vec gensim imprime mensajes `Exception ignored in 'gensim.models.word2vec_inner.our_dot_float'` en stderr; no afectan los resultados (determinismo verificado), pero ensucian la salida de `python src/indices.py`.
9. `bm25` reporta vocabulario 24,971 (sin min_df/max_df, como exige la skill) frente a 13,350 de count/tfidf; `svd`/`lda` reportan el vocabulario de tfidf/count. Coherente, pero conviene mencionarlo en la evaluación.
10. No existe `reports/indices.md` narrativo; la skill solo exige `indices.json`, `lda_topicos.csv`, la figura y `ejemplos_busqueda.md`, por lo que no es FAIL.
11. `ingesta.py` no se ejecutó contra los archivos reales (solo con rutas parametrizadas sobre copias); la rama de CLI `--archivo` se revisó por lectura, no se ejecutó.

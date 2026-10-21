---
name: evaluacion
description: Evalúa y compara los métodos de recuperación de un corpus con categoría (count, tfidf, bm25, svd, w2v, lda) con métricas de ranking (P@k, MAP@10, nDCG@10, MRR) y latencia, usando la categoría como criterio de relevancia. Úsala en la etapa evaluacion del pipeline.
---

# Evaluación de la recuperación

Si el corpus trae juicios de relevancia, úsalos. Si no los trae, se usa la **categoría como proxy**: un documento recuperado es relevante si tiene la misma categoría que la consulta. Este supuesto debe decirse explícitamente en el reporte y en la presentación.

## Conjuntos de consultas

Crea `src/consultas.py` que genere `data/processed/consultas.csv` con columnas `query_id, query, categoria_esperada, tipo, doc_origen`:

1. **Automáticas (tipo = `auto`)**: muestreo estratificado de `evaluacion.auto_por_categoria` documentos por categoría con `random_state=<proyecto.semilla>`. La consulta es el `titulo` del documento. Cada categoría debe tener más documentos que `auto_por_categoria`; si alguna no llega, detente y repórtalo. Guarda su `doc_id` en `doc_origen`: ese documento **se excluye** de su propio ranking (si no, todos los métodos lo encuentran trivialmente).
2. **Manuales (tipo = `manual`)**: las de `evaluacion.consultas_manuales` en `proyecto.yaml`, con su categoría. Deben ser consultas temáticas cortas (2 a 4 palabras), escritas en el idioma del corpus, y el mismo número por categoría (se recomiendan 3). Si `proyecto.yaml` no las trae, detente y pídelas: no las inventes.

## Métricas (`src/evaluacion.py`)

Para cada método y cada consulta, recupera top-10 con `buscar()` (excluyendo `doc_origen`) y calcula:

- **P@5** y **P@10**: relevantes en top-k / k.
- **AP@10** → **MAP@10**: promedio de la precisión en cada posición relevante, dividido entre min(10, total de relevantes en el corpus sin contar `doc_origen`).
- **nDCG@10**: ganancia binaria (1 relevante, 0 no), descuento `1/log2(pos+1)`; IDCG con min(10, total de relevantes) relevantes.
- **MRR**: 1 / posición del primer relevante (0 si no hay).
- **Latencia**: tiempo medio por consulta en milisegundos (mide con `time.perf_counter`, excluye la carga de modelos).

Implementa las métricas tú mismo en funciones pequeñas y **pruébalas** con un caso a mano (p. ej. relevancia `[1,0,1,0,0,0,0,0,0,0]` → P@5 = 0.40) usando `assert` dentro del script.

## Salidas

1. `reports/metricas_por_consulta.csv` (método, query_id, tipo, cada métrica).
2. `reports/metricas.csv`: promedio por método y tipo de consulta (auto / manual / total). Columnas en este orden: `metodo, tipo, p_at_5, p_at_10, map_at_10, ndcg_at_10, mrr, latencia_ms`. Valores con 4 decimales en el CSV.
3. `reports/metricas_por_categoria.csv`: MAP@10 por método y categoría.
4. Gráficas en `reports/figuras/` con la paleta del proyecto:
   - `eval_map_por_metodo.png`: barras de MAP@10 por método (ordenadas de mayor a menor).
   - `eval_heatmap_categoria.png`: método × categoría con MAP@10 (matplotlib `imshow`, valores anotados).
   - `eval_latencia.png`: latencia por método.
5. `reports/evaluacion.md` con:
   - El supuesto de relevancia y sus limitaciones.
   - Tabla resumen (porcentajes con 2 decimales, p. ej. `P@10 = 87.35%`).
   - Para cada diferencia entre métodos que se mencione, un intervalo de confianza de 95% por bootstrap pareado sobre las consultas (`random_state=<semilla>`); si incluye 0, dilo y no declares ganador.
   - Método ganador global y por tipo de consulta, y **por qué** (p. ej. BM25 premia coincidencia exacta en consultas cortas; SVD/W2V captan sinónimos; LDA es demasiado grueso con 10 tópicos).
   - 2 casos donde los métodos discrepan: consulta, top-3 de cada método, explicación.
   - 3 hallazgos en una frase cada uno, listos para usarse como titulares de diapositiva.

## No hagas

- No cambies parámetros de los índices aquí. Si un método sale muy mal, repórtalo; el ajuste se hace volviendo a la etapa `indices`.

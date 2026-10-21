---
name: evaluacion
description: Evalúa y compara los métodos de recuperación (count, tfidf, bm25, svd, w2v, lda) con métricas de ranking (P@k, MAP@10, nDCG@10, MRR) y latencia, eligiendo el criterio de relevancia y las consultas según lo que traigan los datos (juicios de relevancia, categorías o ninguno). Úsala en la etapa evaluacion del pipeline.
---

# Evaluación de la recuperación

Lee la sección `evaluacion` de `proyecto.yaml`. Respeta lo fijado; decide lo que esté en `auto` con las reglas de abajo, escríbelo de vuelta y regístralo en `decisiones` con su razón.

## Decide según los datos: el criterio de relevancia

`evaluacion.modo` lo propuso `eda_raw`; confírmalo aquí:

| Modo | Cuándo | Relevante es… | Consultas |
|---|---|---|---|
| `juicios` | Hay juicios de relevancia (archivo de qrels o consultas con sus documentos correctos) | lo que digan los juicios | las de los juicios |
| `categoria` | Hay categorías y no hay juicios | todo documento con la misma categoría que la consulta | automáticas + manuales (abajo) |
| `item_conocido` | No hay categorías ni juicios | el documento del que salió la consulta (y sus casi duplicados, similitud ≥ 0.95) | automáticas |

El criterio elegido y sus limitaciones se dicen explícitamente en el reporte y en la presentación. En `categoria`, las métricas miden "acierto de categoría", no satisfacción del usuario; en `item_conocido`, miden si el método encuentra un documento concreto a partir de un fragmento suyo.

## Decide según los datos: las consultas (si está en `auto`)

| Clave | Regla |
|---|---|
| `auto_por_categoria` | Modo `categoria`: `min(20, ⌊tamaño de la categoría más pequeña / 5⌋)`, y al menos 5. Si alguna categoría tiene menos de 25 documentos, avisa. |
| `n_auto` | Modo `item_conocido`: `min(200, ⌊D / 10⌋)`, y al menos 50. |
| `consultas_manuales` | Modo `categoria`: 3 por categoría (como máximo 12 categorías, las más grandes), escritas por ti en el idioma del corpus a partir de los términos característicos de cada categoría en `reports/eda_corpus.md`: consultas temáticas de 2 a 4 palabras, como las escribiría una persona. Regístralas y di en el reporte que las generó el agente a partir del vocabulario. Si el usuario las fijó, usa las suyas. |
| `n_consultas_minimo` | El número total de consultas generadas (lo usa la validación). |

**Automáticas**: muestreo estratificado por categoría (o aleatorio simple en `item_conocido`) con `random_state=<semilla>`. La consulta es el `titulo` del documento; si el título es el propio inicio del texto (no hay columna de título), sirve igual. Guarda el `doc_id` en `doc_origen`: en modo `categoria` ese documento **se excluye** de su propio ranking (si no, todos los métodos lo encuentran trivialmente); en `item_conocido` es justo el que hay que encontrar.

Crea `src/consultas.py` que genere `data/processed/consultas.csv` con columnas `query_id, query, categoria_esperada, tipo, doc_origen` (`categoria_esperada` vacía en `item_conocido`).

## Métricas (`src/evaluacion.py`)

Para cada método y cada consulta, recupera el top-10 con `buscar()` (en modo `categoria`, pide `k=11`, quita `doc_origen` y quédate con 10) y calcula:

- **P@5** y **P@10**: relevantes en top-k / k.
- **AP@10** → **MAP@10**: suma de la precisión en cada posición relevante, dividida entre min(10, total de relevantes en el corpus para esa consulta, sin contar `doc_origen`).
- **nDCG@10**: ganancia binaria, descuento `1/log2(pos+1)`; IDCG con min(10, total de relevantes).
- **MRR**: 1 / posición del primer relevante (0 si no hay).
- En `item_conocido` añade **Éxito@1, @5 y @10** (si el documento buscado está en el top-k) y no reportes P@k, que con un solo relevante no informa.
- **Latencia**: tiempo medio por consulta en milisegundos (`time.perf_counter`, sin contar la carga de modelos: haz una consulta de calentamiento por método).
- Si un método devuelve menos de 10 resultados, las posiciones faltantes cuentan como no relevantes y la consulta sí entra al promedio; reporta cuántas veces pasó.

Implementa las métricas tú mismo en funciones pequeñas y **pruébalas** con casos a mano usando `assert` dentro del script (p. ej. relevancia `[1,0,1,0,0,0,0,0,0,0]` → P@5 = 0.40; todo relevante → 1.0; nada relevante → 0.0).

**Comparaciones**: para cada par de métodos que el reporte compare, calcula un intervalo de confianza de 95% por bootstrap pareado sobre las consultas (`random_state=<semilla>`, 2,000 remuestreos). Si incluye 0, dilo y no declares ganador.

## Salidas

1. `reports/metricas_por_consulta.csv` (método, query_id, tipo, cada métrica).
2. `reports/metricas.csv`: promedio por método y tipo de consulta (cada tipo y `total`). Primeras columnas en este orden: `metodo, tipo`, luego las métricas del modo y al final `latencia_ms`. Modo `categoria`: `p_at_5, p_at_10, map_at_10, ndcg_at_10, mrr`. Modo `item_conocido`: `exito_at_1, exito_at_5, exito_at_10, mrr, ndcg_at_10`. Valores con 4 decimales.
3. `reports/metricas_por_categoria.csv`: MAP@10 por método y categoría (solo con categorías). Si las categorías están desbalanceadas, reporta también el promedio macro por categoría.
4. Gráficas en `reports/figuras/` con la paleta del proyecto:
   - `eval_map_por_metodo.png`: la métrica principal por método (MAP@10, o MRR en `item_conocido`), ordenada de mayor a menor.
   - `eval_heatmap_categoria.png`: método × categoría (`imshow`, valores anotados). Sin categorías: método × tipo de consulta.
   - `eval_latencia.png`: latencia por método.
5. `reports/evaluacion.json` con las métricas, los intervalos de confianza y los casos candidatos a discrepancia.
6. `reports/evaluacion.md` con:
   - El criterio de relevancia y sus limitaciones.
   - Tabla resumen (porcentajes con 2 decimales, p. ej. `P@10 = 87.35%`).
   - Método ganador global y por tipo de consulta, y **por qué**, respaldado por los intervalos.
   - 2 casos donde los métodos discrepan: consulta, top-3 de cada método, explicación.
   - Una sección `## Hallazgos` con 3 hallazgos de una frase cada uno, listos para titulares de diapositiva, que no afirmen más de lo que muestran los intervalos.

## No hagas

- No cambies parámetros de los índices aquí. Si un método sale muy mal, repórtalo; el ajuste se hace volviendo a la etapa `indices`.
- No cambies un valor de `proyecto.yaml` que el usuario fijó (sin `auto`).

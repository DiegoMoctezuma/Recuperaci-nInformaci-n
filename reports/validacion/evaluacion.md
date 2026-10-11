# Validación de la etapa `evaluacion`

- Fecha: 2026-10-11
- Resultado: **PASS** (6/6 verificaciones del checklist; `src/validar.py --etapa evaluacion` salió con código 0)
- Revisor independiente: no ejecutó `src/evaluacion.py` ni `src/consultas.py`; todo recalculado en memoria.

## Verificaciones del checklist

| id | descripción | resultado | detalle |
|---|---|---|---|
| V1 | métricas agregadas | PASS | reports/metricas.csv existe |
| V2 | los 4 métodos evaluados | PASS | |
| V3 | métricas entre 0 y 1 | PASS | min 0.6496, max 1.0000 (sin latencia) |
| V4 | 100 auto + 15 manuales | PASS | 115 query_id únicos |
| V5 | gráficas de evaluación | PASS | las 3 PNG existen |
| V6 | reporte de evaluación | PASS | reports/evaluacion.md existe |

## Revisión cualitativa (verificaciones propias)

1. **Consultas**: columnas exactas; 100 auto (20 por categoría) + 15 manual (3 por categoría); query_id únicos. Reproducido el muestreo (`corpus[category==c].sample(20, random_state=42)`, ordenado por doc_id): mismos 100 doc_origen en el mismo orden. Query de cada auto == `titulo` del doc_origen (máx. 8 palabras) y categoría coincide. Las 15 manuales son exactamente las de la skill, con su categoría y doc_origen vacío.
2. **Métricas** con implementación propia (6 métodos x 115 consultas = 690 filas, `buscar(k=11)`, excluyendo doc_origen, top-10, divisor de AP = min(10, relevantes sin doc_origen)): diferencia máxima vs metricas_por_consulta.csv = 4.94e-05 (nDCG; P@5 y P@10 exactas); vs metricas.csv (18 filas) = 4.93e-05; vs metricas_por_categoria.csv (30 filas) = 4.86e-05. Todo dentro de la tolerancia 1e-4 (redondeo a 4 decimales).
3. **metricas.csv**: columnas exactas y en orden; 18 filas (6 x auto/manual/total); 4 decimales en el archivo; métricas en [0,1]; latencia > 0.
4. **src/evaluacion.py**: `_pruebas_metricas()` con `assert` (incluye [1,0,1,0,0,0,0,0,0,0] -> P@5 = 0.40, AP, nDCG, RR, casos todo/nada); latencia con `time.perf_counter` alrededor de `buscar()` con una consulta de calentamiento por método (excluye carga de modelos); no hay `fit` ni cambio de parámetros de índices. Importable sin efectos: se importó `evaluacion` y `consultas` y no cambió el mtime de ningún archivo (salvo `__pycache__`).
5. **reports/evaluacion.md**: supuesto de relevancia y limitaciones explícitos; tabla resumen con porcentajes a 2 decimales: las 6 filas totales y las 6 filas de MAP@10 por tipo coinciden con metricas.csv (0 discrepancias); mejor/peor categoría coinciden con metricas_por_categoria.csv; ganador global y por tipo con explicación; 2 casos (auto_064 y auto_063) con top-3 de los 6 métodos: **ambos verificados re-ejecutando `buscar()`, los 36 top-3 coinciden** y los AP@10 citados también; 3 hallazgos bajo "## Hallazgos". La ventaja de Word2Vec sobre SVD se reporta como no concluyente (+3.89 puntos, IC 95% [-0.38, 8.22], "no se puede afirmar que sea mejor"); mi bootstrap independiente da [-0.33, 8.03], mismo veredicto. Otras cifras citadas (SVD vs BM25 +10.06, IC [6.62, 13.57], 55/14 consultas; BM25 vs TF-IDF +1.49, IC incluye 0; SVD 3.7x más lento que W2V; mínimo 347 documentos por categoría; doc_0150/doc_0834 duplicados PlayStation) verificadas. Formato: miles con coma (2,126), porcentajes con 2 decimales.
6. **Figuras** (vistas): barras ordenadas de mayor a menor (w2v, svd, lda, bm25, tfidf, count), valores 0.8817...0.6870 coinciden con el CSV; heatmap con `imshow`, valores anotados que coinciden con metricas_por_categoria.csv; latencia por método con valores iguales a metricas.csv (12.09 ... 2.46). Las tres con título y ejes rotulados, legibles; sin seaborn (matplotlib puro).
7. **Entradas intactas**: SHA-256 de corpus_clean.csv idéntico al inicio y al final (4920512e...cc9eb0). `git status --short`: solo `estado/progreso.json` modificado entre los versionados; el resto son archivos nuevos de la etapa.

## Advertencias (no bloqueantes)

- Hallazgo 2: afirma que BM25 y TF-IDF "superan al conteo simple"; BM25 vs count es significativo (IC [1.47, 9.71]) pero TF-IDF vs count no (IC en evaluacion.json [-0.35, 8.15], incluye 0). Matizar en una revisión posterior.
- Los hallazgos son frases largas con varias cláusulas; la skill pide "una frase cada uno, listos como titulares". Se cumple la letra (una frase), pero habría que acortarlos en la etapa de presentación.
- Consultas manuales en el techo (SVD y W2V 100%, el peor 93.64%): discriminan poco; el reporte lo declara. El "ganador" por tipo manual es un empate.
- Duplicados casi exactos del doc_origen no se excluyen (declarado en el reporte).
- Ganador global W2V (MAP@10 88.17%): respaldado por los números pero no concluyente frente a SVD (SVD tiene mejor MRR); el reporte lo dice. LDA iguala a BM25 en MAP@10 (IC [-7.25, 8.14]).
- `reports/evaluacion.json` es un extra no pedido por la skill (intervalos bootstrap, casos candidatos); no contradice la skill.
- `reports/evaluacion.md` está escrito a mano y sus cifras de latencia corresponden a la última corrida (coinciden con metricas.csv actual); re-ejecutar `evaluacion.py` cambiaría la latencia y lo desincronizaría.
- La latencia incluye preprocesamiento de la consulta + búsqueda (declarado); la latencia alta de count (12.09 ms) queda sin explicar (declarado).
- No se ejercitó la regeneración de archivos con `python src/evaluacion.py` (por instrucción); se verificó que sus métricas coinciden con una implementación independiente.
- Los IC bootstrap del reporte no son bit a bit reproducibles con mi semilla (diferencias de ~0.3 puntos en los extremos), sin efecto en las conclusiones.

## Instrucciones de corrección

No aplica (PASS).

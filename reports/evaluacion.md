# Evaluación de la recuperación (etapa 6)

Se evalúan los 6 métodos (`count`, `tfidf`, `bm25`, `svd`, `w2v`, `lda`) sobre 115 consultas (100 automáticas + 15 manuales) contra el corpus de 2,126 documentos BBC News. Todas las métricas se calculan sobre el top-10 de `buscar()`. Los números salen de `reports/metricas.csv`, `reports/metricas_por_consulta.csv`, `reports/metricas_por_categoria.csv` y `reports/evaluacion.json` (regenerables con `python src/consultas.py` y `python src/evaluacion.py`).

## Supuesto de relevancia y limitaciones

**Supuesto: la categoría es el proxy de relevancia.** El corpus no trae juicios de relevancia, así que un documento recuperado se considera relevante si su categoría coincide con la categoría esperada de la consulta. Este supuesto debe repetirse en la presentación.

Limitaciones:

- **Categoría no es relevancia real.** Un documento de la categoría correcta puede no tratar el tema de la consulta (por ejemplo, para una consulta sobre rugby cuenta como relevante una nota de atletismo, ver caso 1), y un documento de otra categoría puede ser perfectamente relevante (una nota de negocios sobre patrocinio deportivo). Las métricas miden "acierto de categoría", no satisfacción del usuario.
- **Relevancia binaria y de una sola etiqueta**: no hay grados de relevancia y las fronteras entre categorías (business/politics, tech/business) son difusas, lo que penaliza a todos los métodos por igual pero no necesariamente de forma uniforme.
- **Consultas automáticas**: son las primeras 8 palabras de un documento (titulares, a veces truncados), no consultas reales de usuarios. Se excluye el documento de origen de su propio ranking, pero no sus posibles duplicados casi exactos en el corpus (por ejemplo `doc_0150` y `doc_0834` sobre PlayStation), que pueden inflar un poco los resultados.
- **Consultas manuales**: solo 15 (3 por categoría) y muy fáciles; varios métodos llegan a 100.00% (techo), por lo que no discriminan.
- **Muestra pequeña**: con 115 consultas, diferencias de 1 a 4 puntos pueden no ser estadísticamente distinguibles (ver intervalos bootstrap más abajo).
- Como toda categoría tiene más de 10 documentos (el mínimo es 347), el divisor de AP@10 es siempre 10 y el IDCG de nDCG@10 usa 10 relevantes.
- La latencia incluye el preprocesamiento de la consulta (`preprocesar`) y la búsqueda, y excluye la carga de modelos (hay una consulta de calentamiento por método). Varía entre ejecuciones; las demás métricas son deterministas (`random_state=42`).

Resultados incompletos (método devolvió menos de 10 resultados tras excluir `doc_origen`): **0 de 115 consultas en los 6 métodos**; no hubo consultas vacías.

## Tabla resumen (las 115 consultas, tipo = total)

| Método | P@5 | P@10 | MAP@10 | nDCG@10 | MRR | Latencia (ms) |
|---|---|---|---|---|---|---|
| w2v | 90.96% | 90.96% | **88.17%** | 91.10% | 94.14% | 2.46 |
| svd | 90.43% | 86.87% | 84.28% | 88.58% | 96.39% | 9.16 |
| lda | 77.22% | 78.78% | 74.56% | 78.56% | 83.09% | 2.65 |
| bm25 | 84.17% | 78.96% | 74.22% | 81.85% | 95.93% | 4.17 |
| tfidf | 82.61% | 78.70% | 72.73% | 80.98% | 93.91% | 4.48 |
| count | 77.91% | 74.87% | 68.70% | 76.76% | 89.59% | 12.09 |

MAP@10 por tipo de consulta:

| Método | auto (100) | manual (15) | total (115) |
|---|---|---|---|
| w2v | **86.39%** | 100.00% | 88.17% |
| svd | 81.92% | 100.00% | 84.28% |
| lda | 71.17% | 97.21% | 74.56% |
| bm25 | 70.77% | 97.18% | 74.22% |
| tfidf | 69.07% | 97.14% | 72.73% |
| count | 64.96% | 93.64% | 68.70% |

MAP@10 por categoría esperada (23 consultas por categoría y método; mejor y peor categoría de cada método):

| Método | Mejor categoría | Peor categoría |
|---|---|---|
| w2v | business 92.04% | politics 82.87% |
| svd | tech 92.29% | politics 78.88% |
| lda | business 86.66% | politics 58.36% |
| bm25 | tech 81.61% | entertainment 65.00% |
| tfidf | tech 78.74% | entertainment 65.47% |
| count | tech 80.65% | entertainment 56.93% |

La matriz completa está en `reports/metricas_por_categoria.csv` y en `reports/figuras/eval_heatmap_categoria.png`.

## Método ganador y por qué

- **Global: Word2Vec** (MAP@10 = 88.17%, P@10 = 90.96%, nDCG@10 = 91.10%), seguido de SVD (84.28%). Sobre BM25 la ventaja de SVD es clara (+10.06 puntos de MAP@10; IC 95% bootstrap [6.62, 13.57]; SVD gana en 55 consultas y BM25 en 14). **Entre Word2Vec y SVD la diferencia es +3.89 puntos con IC 95% [-0.38, 8.22]: Word2Vec lidera, pero con 115 consultas no se puede afirmar que sea mejor que SVD.** SVD tiene el mejor MRR global (96.39% frente a 94.14%): acierta algo más a menudo en el primer resultado.
- **Consultas automáticas (titulares de 8 palabras): Word2Vec** (86.39%), después SVD (81.92%). Estas consultas son largas, con nombres propios y palabras genéricas ("battle", "young", "short"); los métodos que representan semánticamente la consulta (SVD, W2V) enlazan con documentos del mismo tema aunque no compartan las palabras exactas, mientras que los léxicos se anclan en coincidencias de palabras sueltas, a veces genéricas.
- **Consultas manuales (2-4 palabras, temáticas): empate entre SVD y Word2Vec** (100.00% en todas las métricas). Con consultas cortas y temáticas casi todos aciertan (el peor, count, llega a 93.64%), así que esta partición apenas discrimina.
- **BM25 frente a TF-IDF**: BM25 queda por delante en todas las métricas (MAP@10 74.22% frente a 72.73%), pero la diferencia (+1.49 puntos, IC 95% [-0.15, 3.21]) es pequeña y su intervalo incluye 0; en la práctica son equivalentes. Count (68.70%) es el peor: sin ponderación por rareza de término, las palabras frecuentes dominan el coseno (BM25 supera a count en +5.52 puntos, IC [1.47, 9.71]).
- **LDA** con 10 tópicos es grueso: su MAP@10 (74.56%) iguala a BM25 (diferencia +0.34 puntos, IC [-7.25, 8.14]), pero tiene el peor MRR (83.09%) y el peor P@5 (77.22%) de los seis, y es el más débil en politics (58.36%). Un tópico agrupa documentos de varias categorías (p. ej. el tópico 5, "Yukos, deuda y Rusia (mixto)", en `reports/lda_topicos.csv`) y la consulta puede caer en el tópico equivocado; cuando acierta, devuelve muchos documentos de la categoría (caso 2).
- **Latencia**: todos están por debajo de 13 ms por consulta. Word2Vec es el más rápido (2.46 ms) y el más preciso; SVD es unas 3.7 veces más lento que Word2Vec (9.16 ms) y count el más lento (12.09 ms). No se investigó la causa de la latencia de count; las diferencias absolutas son de milisegundos.

## Dos casos donde los métodos discrepan

Se tomaron de `reports/evaluacion.json` (candidatos con mayor dispersión de AP@10 entre métodos, una consulta automática de cada tipo de patrón). `doc_origen` ya está excluido.

### Caso 1: `auto_064` "white prepared for battle tough-scrummaging prop julian white" (esperado: sport)

AP@10 por método: svd 1.0000, w2v 1.0000, tfidf 0.8900, bm25 0.8521, count 0.7004, lda 0.0000.

| Método | Top-3 |
|---|---|
| count | doc_0333 (sport) white admits to balco drugs link; doc_0721 (sport) mansfield 0-1 leyton orient; doc_0357 (politics) baa support ahead of court battle |
| tfidf | doc_0333 (sport) white admits to balco drugs link; doc_1245 (sport) barkley fit for match in ireland; doc_2044 (sport) bell set for england debut |
| bm25 | doc_1245 (sport) barkley fit for match in ireland; doc_2044 (sport) bell set for england debut; doc_0057 (sport) henson stakes early lions claim |
| svd | doc_1472 (sport) vickery out of six nations; doc_2044 (sport) bell set for england debut; doc_1650 (sport) stevens named in england line-up |
| w2v | doc_1650 (sport) stevens named in england line-up; doc_1245 (sport) barkley fit for match in ireland; doc_0978 (sport) dawson wins england squad recall |
| lda | doc_1999 (business) beer giant swallows russian firm; doc_1515 (business) chinese wine tempts italy; doc_1695 (business) india s deccan seals $1.8bn deal |

Explicación: la consulta es un titular de rugby (pilier inglés, Seis Naciones). Count y TF-IDF colocan primero `doc_0333`, una nota de atletismo que solo comparte el apellido "white" (cuenta como relevante por ser de la categoría sport, pero no trata de rugby; aquí se ve la limitación del proxy), y count además mete en el top-3 un documento de política que comparte "battle". BM25 evita esa coincidencia de apellido y recupera notas de rugby. SVD y W2V devuelven solo notas de rugby inglés, es decir, captan el tema aunque no coincidan las palabras. LDA falla por completo: los tres primeros son de business. Es una explicación plausible a partir de los resultados, no comprobada: la mezcla de tópicos de la consulta corta y con nombres propios cae en un tópico de negocios.

### Caso 2: `auto_063` "young debut cut short by ginepri fifteen-year-old donald" (esperado: sport)

AP@10 por método: lda 1.0000, w2v 0.2595, tfidf 0.0900, bm25 0.0200, count 0.0000, svd 0.0000.

| Método | Top-3 |
|---|---|
| count | doc_1268 (politics) short attacks us over tsunami aid; doc_1907 (politics) tories unveil quango blitz plans; doc_1636 (business) us airways staff agree to pay cut |
| tfidf | doc_0590 (entertainment) branson show flops on us screens; doc_0714 (sport) rochus shocks coria in auckland; doc_1765 (business) us gives foreign firms extra time |
| bm25 | doc_0590 (entertainment) branson show flops on us screens; doc_1765 (business) us gives foreign firms extra time; doc_1725 (politics) brown names 16 march for budget |
| svd | doc_0772 (entertainment) bollywood draws global stars; doc_1119 (business) mcdonald s to sponsor mtv show; doc_1027 (entertainment) tough schedule delays elliot show |
| w2v | doc_2072 (entertainment) briton wins short film oscar; doc_1175 (sport) what now for british tennis; doc_1786 (sport) o connor aims to grab opportunity |
| lda | doc_0554 (sport) mcilroy continues winning streak; doc_0836 (sport) gardener wins double in glasgow; doc_1059 (sport) off-colour gardener storms to win |

Explicación: es un titular de tenis con un nombre propio poco frecuente ("ginepri") y palabras genéricas. Los métodos léxicos (count, TF-IDF, BM25) se quedan con coincidencias genéricas ("short", "us", "cut", "pay") y devuelven política, negocios y entretenimiento. SVD tampoco rescata la consulta (AP@10 = 0.0000). W2V mezcla "short film" con tenis británico. LDA, que opera con 10 tópicos amplios, asigna la consulta a un tópico deportivo y devuelve notas de deporte (un acierto que aquí se debe a que el tópico grueso coincide con la categoría; no es evidencia general de que LDA sea mejor, ya que en el caso 1 y en el agregado es peor).

## Hallazgos

1. **Word2Vec lidera con 88.17% de MAP@10; SVD le sigue con 84.28% y los métodos léxicos quedan atrás.**
   *Apoyo: la ventaja de Word2Vec sobre SVD (+3.89 puntos, IC 95% [-0.38, 8.22]) no es concluyente con 115 consultas; SVD supera a BM25 (74.22%) por +10.06 puntos, IC [6.62, 13.57]. Word2Vec es además el más rápido (2.46 ms por consulta).*

2. **BM25 (74.22%) y TF-IDF (72.73%) rinden casi igual; solo BM25 supera con claridad al conteo (68.70%).**
   *Apoyo: BM25 frente a TF-IDF, +1.49 puntos, IC [-0.15, 3.21]; BM25 frente a conteo, +5.52 puntos, IC [1.47, 9.71]; TF-IDF frente a conteo, +4.03 puntos, IC [-0.35, 8.15] (incluye 0).*

3. **Con consultas manuales cortas casi todos aciertan; con titulares de 8 palabras Word2Vec logra 86.39% y conteo 64.96%.**
   *Apoyo: en las 15 consultas manuales SVD y Word2Vec alcanzan 100.00% de MAP@10 y el peor, conteo, 93.64%.*

## Archivos

`src/consultas.py`, `src/evaluacion.py`, `data/processed/consultas.csv`, `reports/metricas_por_consulta.csv`, `reports/metricas.csv`, `reports/metricas_por_categoria.csv`, `reports/evaluacion.json`, `reports/figuras/eval_map_por_metodo.png`, `reports/figuras/eval_heatmap_categoria.png`, `reports/figuras/eval_latencia.png`.

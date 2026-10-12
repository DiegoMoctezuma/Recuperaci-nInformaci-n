# Guion del video — "La consulta fácil engaña"

Escrito con `skills/video-storytelling/SKILL.md`. Estado: **aprobado y producido** (`video/salida/bbc_news_ir.mp4`). La narración es la de `video/escenas.json`.

## Audiencia

- **Quién es**: el profesor de la materia, experto en recuperación de información.
- **Qué sabe ya (se deja fuera)**: qué son TF-IDF, BM25, LSA, Word2Vec y LDA; qué miden P@k, MAP, nDCG y MRR; las leyes de Zipf y Heaps. No se define nada de esto.
- **Qué queremos que sepa al final**:
  1. En este corpus, con consultas difíciles, las representaciones semánticas superan a las léxicas por más de 10 puntos de MAP@10.
  2. Las consultas fáciles esconden esa diferencia: con ellas todos los métodos parecen buenos.
  3. Sabemos hasta dónde llega nuestra evidencia: la relevancia es un proxy y el primer lugar no está decidido.
- **Pitch**: jerga técnica completa, sin glosas.
- **Tone**: conversacional y sobrio, de colega a colega. Nada de tono de anuncio.
- **Héroe**: quien tiene que elegir cómo buscar en un archivo de noticias (el espectador, tratado de "tú"). **Guía**: el equipo, que ya hizo el recorrido y lo midió.

## Escenas

Duración total: 96 segundos. Narración: 195 palabras (2.0 palabras por segundo, con aire para que se lean las cifras).

| # | Bloque / paso | Tiempo | Narración | En pantalla | Visual | Fuente | Pilar |
|---|---|---|---|---|---|---|---|
| 1 | Paisaje · mundo ordinario | 0–8 s | Un archivo de noticias crece todos los días. El nuestro, de la BBC, guarda dos mil doscientas veinticinco. | **2,225** noticias · 5 categorías | archivo: rotativa imprimiendo y estantes de hemeroteca | `reports/eda_raw.json` → `n_docs`, `conteo_categorias` | Pathos |
| 2 | Desafíos · llamada a la aventura | 8–17 s | Y tú necesitas una sola. No recuerdas el titular completo, solo un pedazo: ocho palabras. | `lost doors frontman movie found historians in florida` | captura real: la consulta tecleándose en una barra de búsqueda | `data/processed/consultas.csv` → `auto_023` | Pathos |
| 3 | Desafíos · rechazo de la llamada | 17–28 s | Lo tentador es quedarse con lo de siempre y probarlo con consultas cortas. Ahí todo funciona: hasta contar palabras acierta noventa y tres por ciento. | Consultas manuales · conteo **93.64%** | gráfica animada: seis barras casi iguales, todas arriba | `reports/metricas.csv` → `count`, `manual`, `map_at_10` | Logos |
| 4 | Soluciones · encuentro con el guía | 28–38 s | Nosotros ya hicimos ese recorrido. Seis métodos, ciento quince consultas y un mismo preprocesamiento para el corpus y para la consulta. | 6 métodos · **115** consultas · 2,126 documentos | gráfica animada: los seis nombres entrando en fila | `reports/evaluacion.json` → `n_consultas`; `reports/limpieza.json` → `n_despues` | Ethos |
| 5 | Soluciones · cruzar el umbral y aliados | 38–48 s | Antes de medir, limpiamos: noventa y nueve duplicados fuera. Y comprobamos que el corpus se comporta como lenguaje. | 99 duplicados · Heaps **β = 0.5387** | gráfica animada: la curva de Heaps dibujándose | `reports/limpieza.json` → `duplicados`; `reports/eda_corpus.json` → `heaps_beta` | Ethos |
| 6 | Soluciones · acercamiento a la cueva | 48–57 s | Luego buscamos la prueba difícil: cien titulares de ocho palabras, sin el documento del que salieron. | **100** titulares · documento de origen excluido | archivo: recortes de periódico pasando | `data/processed/consultas.csv` → `tipo = auto`; `reports/evaluacion.md` → limitaciones | Logos |
| 7 | Puntos de prueba · la prueba | 57–69 s | Mira tu consulta. BM25 se ancla en palabras sueltas y trae tenis y tecnología. Word2Vec devuelve cinco de cinco notas de entretenimiento. | BM25: AP@10 **0.36** · Word2Vec: AP@10 **1.00** | captura real: los dos top-5 lado a lado, con la categoría de cada resultado | `reports/metricas_por_consulta.csv` → `auto_023`; `src/buscar.py` con `bm25` y `w2v` | Logos |
| 8 | Puntos de prueba · la recompensa | 69–79 s | En las ciento quince consultas, Word2Vec llega a ochenta y ocho por ciento de MAP a diez. BM25 se queda en setenta y cuatro. | Word2Vec **88.17%** · SVD 84.28% · BM25 74.22% | gráfica animada: barras de MAP@10 ordenadas | `reports/metricas.csv` → `total`, `map_at_10` | Logos |
| 9 | Puntos de prueba · camino de regreso | 79–88 s | Dos advertencias. Relevante aquí significa misma categoría. Y entre Word2Vec y SVD, la muestra no alcanza para declarar un ganador. | Relevante = misma categoría · IC 95% **[-0.38, 8.22]** | gráfica animada: las dos barras superiores con su intervalo | `reports/evaluacion.md` → supuesto de relevancia e intervalos | Ethos |
| 10 | Resumen · resurrección y elixir | 88–96 s | Ahora sabes qué elegir y qué medir después: representación semántica hoy, juicios de relevancia reales mañana. | Buscar por tema, no por palabra exacta | archivo: una mano encuentra un ejemplar en el estante | conclusión de `reports/evaluacion.md` | Pathos |

## Las tres ideas y dónde aparecen

| Idea | Escenas | Cifra |
|---|---|---|
| Lo semántico supera a lo léxico en consultas difíciles | 7 y 8 | 88.17% frente a 74.22% de MAP@10 |
| Las consultas fáciles esconden la diferencia | 3 y 6 | conteo 93.64% con manuales |
| Conocemos el límite de la evidencia | 9 | IC 95% [-0.38, 8.22]; relevancia por categoría |

## Cifras citadas (para contrastar una a una)

| Cifra | Fuente |
|---|---|
| 2,225 noticias, 5 categorías | `reports/eda_raw.json` |
| 99 duplicados; 2,126 documentos | `reports/limpieza.json` |
| Heaps β = 0.5387 | `reports/eda_corpus.json` |
| 6 métodos; 115 consultas (100 automáticas, 15 manuales) | `reports/evaluacion.json`, `data/processed/consultas.csv` |
| Conteo con consultas manuales: MAP@10 = 93.64% | `reports/metricas.csv` |
| MAP@10 total: Word2Vec 88.17%, SVD 84.28%, BM25 74.22% | `reports/metricas.csv` |
| Consulta `auto_023`: AP@10 de BM25 = 0.36 y de Word2Vec = 1.00 | `reports/metricas_por_consulta.csv` |
| Top-5 de `auto_023`: BM25 trae 2 de entretenimiento, 1 de deporte y 2 de tecnología; Word2Vec, 5 de entretenimiento | `src/buscar.py` (documento de origen `doc_0209` excluido) |
| Word2Vec frente a SVD: +3.89 puntos, IC 95% [-0.38, 8.22] | `reports/evaluacion.md` |

## Recursos por conseguir (camino gratuito)

- **Metraje de archivo** con licencia libre (dominio público o Creative Commons): rotativa de periódico, hemeroteca o estantes de archivo, recortes de prensa, una mano tomando un ejemplar. Cuatro clips de 8 a 10 segundos. Se anota la licencia y la procedencia de cada uno.
- **Gráficas animadas**: generadas desde `reports/` con la paleta y la tipografía de `presentacion/estilo.json`.
- **Capturas reales**: salida de `src/buscar.py` para `auto_023` con `bm25` y `w2v`.
- **Voz**: narración sintética gratuita en español, o grabada por el equipo sobre este mismo guion.
- **Música**: ninguna por ahora; si el equipo aporta una pista con licencia, se mezcla.

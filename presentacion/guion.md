# Guion de la presentación (storytelling)

Supuesto que atraviesa el relato: la **categoría es el proxy de relevancia** (se dice en las diapositivas 11 y 12 y en las notas de 3, 7, 10, 12, 13 y 14).

Los datos de portada (título, equipo, materia, fecha, nombre corto) son provisionales y se editan en `presentacion/slides.json` (diapositiva 1).

## 1. portada — Recuperación de información en BBC News

**Idea:** Presentar el proyecto.

**Notas del orador:** Buenos días. Les presento un sistema de recuperación de información sobre noticias de la BBC. Partimos de 2,225 noticias en cinco categorías, las limpiamos y construimos seis formas de buscar: conteo, TF-IDF, BM25, SVD, Word2Vec y LDA. Las comparamos con 115 consultas. Veremos qué encontramos, qué método rinde mejor y con qué cautelas deben leerse los resultados, empezando por el problema.

## 2. cifra_grande — Encontrar la noticia correcta entre 2,225 exige un buscador, no paciencia

**Idea:** El problema: encontrar la noticia correcta entre 2,225.

**Notas del orador:** El problema es sencillo de enunciar: dada una consulta en lenguaje natural, devolver las noticias más parecidas. Con 2,225 noticias de la BBC repartidas en cinco categorías, leerlas una por una no es práctico. Por eso construimos un buscador y, sobre todo, comparamos seis maneras de representar el texto, porque la elección de esa representación cambia mucho qué documentos aparecen primero.

## 3. grafica — Deporte y negocios suman 45.89% de las 2,225 noticias

**Idea:** El corpus: 5 categorías sin una dominante.

**Notas del orador:** Este es el corpus: cinco categorías, de 386 noticias de entretenimiento a 511 de deporte. Deporte y negocios suman 45.89% de las 2,225 noticias, pero ninguna categoría domina, así que no esperamos un sesgo fuerte hacia un tema. Esto importa porque más adelante usaremos la categoría como criterio de relevancia: un documento es relevante si comparte categoría con la consulta.

## 4. cifra_grande — 99 noticias estaban duplicadas y quedaron 2,126 documentos únicos

**Idea:** Limpieza: de 2,225 a 2,126 documentos (99 duplicados exactos).

**Notas del orador:** Antes de indexar limpiamos el corpus. Encontramos 99 noticias duplicadas exactas, siempre con la misma categoría, y las eliminamos: quedaron 2,126 documentos. Si se dejaran, un duplicado del documento de origen sería un acierto trivial y las métricas saldrían infladas. Después normalizamos el texto, quitamos stopwords y lematizamos, lo que dejó un vocabulario de 24,971 palabras.

## 5. grafica — Pocas palabras dominan el corpus: la frecuencia cae con exponente s = 0.6088

**Idea:** Zipf: pocas palabras dominan (s = 0.6088).

**Notas del orador:** La ley de Zipf dice que pocas palabras concentran muchas apariciones. Ajustamos los rangos 1 a 1,000 y obtuvimos un exponente de 0.6088, con R cuadrada de 0.9469. Es más bajo que el uno clásico porque quitamos las stopwords, que son justo las palabras más frecuentes. El mensaje práctico: unas cuantas palabras pesan mucho, y por eso ponderar por rareza tiene sentido.

## 6. grafica — El vocabulario no deja de crecer: β = 0.5387

**Idea:** Heaps: el vocabulario sigue creciendo (β = 0.5387).

**Notas del orador:** La ley de Heaps mide cuánto crece el vocabulario al leer más texto. Con un exponente beta de 0.5387, dentro del rango típico, el vocabulario sigue creciendo sin estabilizarse: terminamos con 24,971 palabras distintas en 385,689 tokens, y 39.97% aparece una sola vez. Eso significa que siempre habrá consultas con palabras que el índice apenas vio, algo a tener presente al evaluar.

## 7. bloques — Cada categoría tiene su propia huella de palabras

**Idea:** Cada categoría tiene su huella léxica.

**Notas del orador:** Cada categoría tiene su propio vocabulario. Estas nubes muestran deporte, política y tecnología; el tamaño destaca las palabras frecuentes y propias de cada una, no las genéricas. En deporte aparecen nombres como Roddick o Mourinho, en política Tory y UKIP, en tecnología spam y browser. Esta huella léxica justifica usar la categoría como criterio de relevancia, aunque sea un criterio imperfecto.

## 8. flujo — La consulta se convierte en vector y se compara con cada documento

**Idea:** Cómo funciona el buscador.

**Notas del orador:** Así funciona el buscador. La consulta pasa por la misma limpieza que el corpus, se convierte en un vector según el método elegido y se compara con los 2,126 documentos mediante similitud coseno, o con el puntaje BM25. El resultado es un ranking y nos quedamos con los k más cercanos. Lo que cambia entre métodos es sobre todo cómo se construye ese vector.

## 9. bloques — Cuatro maneras de convertir texto en números

**Idea:** Cuatro formas de representar el texto (Word2Vec y LDA se mencionan en notas; Word2Vec entra en la 10).

**Notas del orador:** Cuatro de los métodos evaluados. El conteo, que en código es CountVectorizer, cuenta apariciones. TF-IDF pondera por rareza. BM25 añade saturación de frecuencia y normalización por longitud. SVD comprime la matriz en 200 dimensiones latentes. Además evaluamos Word2Vec y LDA con 10 tópicos; Word2Vec aparece en seguida porque obtuvo el mejor MAP@10 de los seis.

## 10. cifra_grande — Word2Vec lidera con 88.17% de MAP@10; SVD le sigue con 84.28% y los métodos léxicos quedan atrás.

**Idea:** Hallazgo 1 (reports/evaluacion.md): Word2Vec lidera; su ventaja sobre SVD no es concluyente.

**Notas del orador:** Evaluamos con 115 consultas: 100 automáticas y 15 manuales. Como no hay juicios de relevancia, un documento cuenta como relevante si su categoría coincide con la esperada. Con ese supuesto, Word2Vec obtiene 88.17% de MAP@10 y SVD 84.28%. Cuidado: la diferencia de 3.89 puntos tiene un intervalo de confianza de 95% entre -0.38 y 8.22, así que no podemos afirmar que Word2Vec supere a SVD.

## 11. grafica — BM25 (74.22%) y TF-IDF (72.73%) rinden casi igual; solo BM25 supera con claridad al conteo (68.70%).

**Idea:** Hallazgo 2: BM25 y TF-IDF empatan en la práctica; solo BM25 supera claramente al conteo.

**Notas del orador:** Entre los métodos léxicos, BM25 obtiene 74.22% de MAP@10, TF-IDF 72.73% y conteo 68.70%. BM25 supera a TF-IDF por 1.49 puntos, pero el intervalo incluye cero, así que en la práctica son equivalentes; solo la ventaja sobre el conteo es clara, 5.52 puntos. Recordemos que relevante significa misma categoría que la consulta. SVD supera a BM25 por 10.06 puntos, y Word2Vec es además el más rápido, con 2.46 milisegundos.

## 12. grafica_completa — Con consultas manuales cortas casi todos aciertan; con titulares de 8 palabras Word2Vec logra 86.39% y conteo 64.96%.

**Idea:** Hallazgo 3: el tipo de consulta separa a los métodos (gráfica de mancuernas en lugar del heatmap).

**Notas del orador:** Separamos las consultas por tipo. Con las 15 manuales, de dos a cuatro palabras y muy temáticas, SVD y Word2Vec llegan a 100.00% y el peor, el conteo, a 93.64%: casi no discriminan. Con los 100 titulares de ocho palabras, que mezclan nombres propios y palabras genéricas, Word2Vec logra 86.39% y el conteo 64.96%. Las diferencias aparecen en las consultas difíciles. Y la categoría sigue siendo solo un proxy de relevancia.

## 13. demo — Word2Vec responde a una consulta temática con tres noticias de política

**Idea:** Demo real: consulta y top-3 de Word2Vec.

**Notas del orador:** Un ejemplo real con Word2Vec: la consulta election labour party vote. Los tres primeros resultados son de política, la categoría esperada. Los títulos son los primeros términos de cada nota, por eso se ven recortados. Conviene recordar que acierto de categoría no es lo mismo que satisfacción del usuario: una nota de la categoría correcta puede no tratar exactamente el tema consultado.

## 14. cierre — Word2Vec y SVD recuperan mejor que los métodos léxicos, aunque su diferencia aún no es concluyente.

**Idea:** Conclusión y recomendación.

**Notas del orador:** En resumen, Word2Vec y SVD recuperan mejor que los métodos léxicos, pero entre ellos la diferencia no es concluyente con 115 consultas. Recomendamos Word2Vec como método principal, por su precisión y velocidad, SVD como alternativa, y validar con juicios de relevancia reales, porque la categoría es solo un proxy. BM25 sirve como línea base léxica sencilla. Gracias; quedo atento a preguntas.

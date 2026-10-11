# Validación de la etapa `presentacion`

Fecha: 2026-10-11 · Resultado: **PASS** (9/9 verificaciones bloqueantes PASS; `src/validar.py --etapa presentacion` salió con código 0)

## Verificaciones del checklist

| id | descripción | resultado |
|---|---|---|
| P1 | sistema de diseño documentado (paleta y tipografía) | PASS |
| P2 | presentación generada | PASS |
| P3 | al menos 12 diapositivas (hay 14) | PASS |
| P4 | sin viñetas | PASS |
| P5 | máx. 60 palabras por diapositiva (máximo real: 53) | PASS |
| P6 | ninguna forma sale del lienzo | PASS |
| P7 | una vista previa por diapositiva (14 + contact_sheet) | PASS |
| P8 | revisión automática sin errores | PASS |
| P9 | revisión visual documentada | PASS |

`checklist_calidad.yaml` de la raíz es idéntico (cmp) al de la skill y trae P1 a P9.

## Comprobaciones independientes (python-pptx propio)

1. Estructura del .pptx: 14 diapositivas, 13.333 x 7.5 in, todas con layout "Blank", 0 placeholders, 0 formas fuera del lienzo, 0 párrafos con viñeta o level > 0, tamaño mínimo 12.0 pt, fuentes solo Georgia (21 runs) y Calibri (87). Palabras por diapositiva: 31, 35, 26, 31, 39, 30, 44, 48, 53, 41, 47, 37, 49, 41. Notas en las 14, de 55 a 71 palabras. Sin tablas.
2. Sistema de diseño: `estilo.json` tiene lienzo, paleta, categorias, tipografia y layouts. Paleta y categorías coinciden con los hex de la skill; añadidos y documentados en `notas`: `acento_texto` #B05400, `superficie` #FFFFFF, `acento_suave` #FBE9D7. Todos los colores de relleno, línea, fondo y texto usados en el .pptx pertenecen a la paleta documentada.
3. Estructura y guion: 14 diapositivas con la secuencia de layouts del Paso 4 (portada, cifra_grande, grafica, cifra_grande, grafica, grafica, bloques, flujo, bloques, cifra_grande, grafica, grafica_completa, demo, cierre). Los títulos 10-12 son literalmente los 3 hallazgos de `reports/evaluacion.md`. Todos los títulos son frases-hallazgo (salvo 7, 8 y 9, que son afirmaciones descriptivas aceptables). `guion.md` y `slides.json` (14 entradas) coherentes con el deck.
4. Veracidad: todas las cifras de texto visible y notas se rastrearon y coinciden (2,225; 2,126; 99 duplicados = 99 grupos de 2 filas, 0 con categorías distintas; 386-511 por categoría; 511+510 = 1,021 = 45.89%; s = 0.6088, R² = 0.9469, rangos 1-1,000; β = 0.5387; V = 24,971; N = 385,689; hapax 39.97%; SVD 200 dim; W2V 100 dim; LDA 10 tópicos; 115 consultas = 100 + 15; MAP@10 88.17 / 84.28 / 74.56 / 74.22 / 72.73 / 68.70; 86.39 / 64.96 / 100.00 / 93.64; 3.89 [-0.38, 8.22]; 10.06; 5.52; 1.49 [-0.15, 3.21]; 2.46 ms; las 15 cifras de la gráfica de mancuernas contra metricas.csv). Palabras de las wordclouds citadas (roddick, nadal, mourinho, wenger, tory, ukip, blunkett, asylum, spam, browser, wifi, psp) están en `eda_corpus.json`. Cifras no rastreables o incorrectas: ninguna.
   - Supuesto "relevante = misma categoría": explícito en diapositivas 11 y 12 (pie) y 14 (recomendación), y en notas de 3, 7, 10, 11, 12, 13 y 14.
   - BM25 no se presenta como ganador (título de la 11 dice que empata con TF-IDF; en la 14 es solo línea base). Word2Vec vs SVD se declara no concluyente en 10 (texto y notas) y 14.
   - Demo (13): `buscar('election labour party vote', 'w2v', 3)` devuelve doc_0259, doc_1208, doc_0375, todos politics, con los mismos títulos que muestra la diapositiva.
5. Formato: miles con coma y porcentajes con 2 decimales en todo el texto visible, salvo "95%" (nivel de confianza del IC) en 10 y 11 y el año 2026 en portada (no son resultados). Texto en español. Sin tablas.
6. Revisión visual: vistas previas 1-14 y contact sheet revisadas; sin desbordes, solapes ni contraste bajo; composición limpia, una idea por diapositiva, sin viñetas disfrazadas; gráficas legibles; figuras PNG RGBA transparentes, 200 dpi (wordclouds a 300 dpi), sin marco superior/derecho, etiquetas directas y un solo elemento en acento.
7. `revision_visual.md`: tiene estado por diapositiva, lista de ICONO pendientes (1 en d1, 5 en d8, 4 en d9 = 10; coincide exactamente con los 10 del .pptx), la nota de revisar en PowerPoint/Keynote/Google Slides y que 6C no estuvo disponible. `revisar.py` implementa de verdad 6A (límites y márgenes, solapes, cabida con métricas de fuente, 12 pt, 60 palabras, viñetas/level, contraste WCAG 4.5, proporción de imágenes, acento, sin transiciones, notas 40-80). Se re-ejecutó (solo reescribe revision_automatica.json): resultado idéntico (errores 0, avisos 0).

Fuentes de datos sin cambios; el único archivo modificado fuera de la etapa es `estado/progreso.json`.

## Decisiones del ejecutor

- a) Tokens añadidos `acento_texto`, `superficie`, `acento_suave`: razonable y documentado (acento da 2.74:1 sobre fondo; la skill exige 4.5:1). Advertencia.
- b) ICONO a 12 pt en lugar de 10 pt: razonable y documentado (choca con el mínimo absoluto de 12 pt). Advertencia.
- c) "Conteo" en vez de "CountVectorizer" en la 9, Word2Vec solo en la 10: razonable, nombre técnico en notas; documentado. Advertencia (el Paso 4 pide cuatro métodos y se cumplen).
- d) Gráfica de mancuernas en la 12: encaja con el espíritu (el título es el hallazgo 3 y la skill pide usar el hallazgo como título) aunque no es literalmente heatmap ni caso de discrepancia; heatmap y latencia se generaron (Paso 3) pero no se usan. Documentado. Advertencia.
- e) Wordclouds ponderadas por frecuencia x proporción propia: razonable, aclarado en el pie. Advertencia.
- f) Datos de portada provisionales: acordado, no es fallo.

## Advertencias

1. Diapositiva 6: en la vista previa el título parte "β =" y "0.5387" en dos líneas, aunque `revision_visual.md` dice que se acortó para evitarlo. Corregir el informe o acortar el título.
2. Diapositiva 5 (texto y notas): "el exponente es bajo porque se quitaron las stopwords" es una explicación causal no respaldada por ningún reporte (eda_corpus.md no la afirma). Suavizar ("posiblemente porque...") o citar fuente.
3. Diapositiva 3: dos barras en acento (deporte y negocios, que son el tema del título); el aviso de "un solo acento" de revisar.py no cuenta imágenes. Los marcadores ICONO tienen borde en acento por especificación.
4. Diapositiva 14: recomienda adoptar Word2Vec mientras afirma que la ventaja sobre SVD no es concluyente; está matizada con SVD como alternativa y validación con juicios reales, pero el verbo "adoptar" es firme.
5. Diapositivas 10-11: "95%" sin decimales (nivel de confianza); título de la 10 agrupa a LDA (74.56%, no léxico) bajo "métodos léxicos quedan atrás", texto heredado del hallazgo 1.
6. Wordclouds a 300 dpi (la skill fija 200 dpi para las gráficas matplotlib); sin impacto.
7. Vista previa aproximada (DejaVu Sans en lugar de Calibri); 6C no disponible; revisar en PowerPoint/Keynote/Google Slides antes de presentar. Los 10 marcadores ICONO siguen pendientes de reemplazo y los datos de portada son provisionales.

## Decisiones pendientes

Ninguna que la skill no cubra. Confirmar con el equipo los datos de portada (equipo, materia, fecha).

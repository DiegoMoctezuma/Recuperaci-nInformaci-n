# Revisión visual de la presentación

**Revisar en PowerPoint/Keynote/Google Slides antes de presentar: la vista previa es aproximada.**

## Cómo se generó y se revisó

Desde la raíz del repo, con el entorno conda `bbc-ir`, en este orden:

```
conda run -n bbc-ir python src/presentacion/diseno.py      # presentacion/estilo.json
conda run -n bbc-ir python src/presentacion/graficas.py    # presentacion/figuras/*.png
conda run -n bbc-ir python src/presentacion/generar.py     # .pptx + preview/ + cajas.json (y estilo.json)
conda run -n bbc-ir python src/presentacion/revisar.py     # revision_automatica.json
```

(`python -m presentacion.generar` también funciona con `PYTHONPATH=src`.) Los textos, cifras, notas y datos de portada se editan en `presentacion/slides.json`; después basta con `generar.py` y `revisar.py`.

## Entorno y fuentes

- Georgia está instalada y se usa tal cual en las vistas previas y en las métricas.
- **Calibri NO está instalada**: el .pptx declara "Calibri", pero las vistas previas, las gráficas (matplotlib) y las métricas de la revisión automática usan DejaVu Sans, que es más ancha. Si el texto cabe con DejaVu, cabe con Calibri; en PowerPoint el texto se verá algo más compacto.
- 6C (LibreOffice/pdftoppm): **no disponible** (`soffice` y `pdftoppm` no están instalados); no se intentó instalarlos.

## Revisión automática (src/presentacion/revisar.py)

Resultado: `errores = 0`, `avisos = 0` (ver `revision_automatica.json`). Comprueba límites del lienzo y de los márgenes, solapes entre cajas de texto, ajuste del texto (líneas × tamaño × 1.2 ≤ alto de la caja), tamaño mínimo de 12 pt, viñetas y niveles, máximo 60 palabras (aviso a partir de 55), contraste WCAG ≥ 4.5:1, proporción de las imágenes, un solo elemento en acento (aviso), ausencia de transiciones y 40–80 palabras en las notas. Máximo de palabras por diapositiva: 53.

## Estado por diapositiva

| Nº | Layout | Estado |
|---|---|---|
| 1 | portada | OK. Se acortó el subtítulo para que no dejara "consultas" huérfana en una segunda línea. |
| 2 | cifra_grande | OK. |
| 3 | grafica | OK. Barras de deporte y negocios en acento, el resto en neutro. |
| 4 | cifra_grande | OK. |
| 5 | grafica | OK. Recta ajustada en acento; los puntos de datos en neutro. |
| 6 | grafica | Corregido: las marcas del eje x se solapaban ("50,000100,000…"); ahora cada 100,000. El primer intento (título alargado) NO resolvió el corte de "β =" / "0.5387"; después se acortó a "El vocabulario no deja de crecer: β = 0.5387" con espacios de no separación entre β, = y la cifra, y se confirmó en la vista previa regenerada. |
| 7 | bloques | OK. Se alinearon las nubes con el texto de los bloques (sangría de 0.1 in). |
| 8 | flujo | OK. Paso clave (Vectores) en acento. |
| 9 | bloques | Corregido: marcadores de icono más grandes (1.7 in) y alineados con el texto; la diapositiva se veía vacía. |
| 10 | cifra_grande | OK. Título = hallazgo 1 de reports/evaluacion.md. |
| 11 | grafica | OK. BM25 en acento solo porque el título habla de BM25 frente a TF-IDF y conteo; no se presenta como ganador. |
| 12 | grafica_completa | OK. Título = hallazgo 3. Gráfica de mancuernas (manual contra automática). |
| 13 | demo | Corregido: la categoría y el título del resultado se solapaban 0.05 in (la revisión automática lo detectó); la barra y las tarjetas se alinearon con el texto del título. |
| 14 | cierre | OK. |

## Decisiones de diseño que conviene conocer

- Paleta ampliada y documentada en `estilo.json` (`notas`): `acento` (#E07A1F) da 2.74:1 sobre el fondo claro y no pasa el contraste de 4.5:1, así que el texto en acento sobre fondo claro usa `acento_texto` (#B05400, 4.64:1). Las barras, la recta y los marcadores siguen usando `acento`; sobre fondo oscuro se usa `acento` (5.30:1). Se añadieron también `superficie` (#FFFFFF, tarjetas) y `acento_suave` (relleno del marcador del paso clave).
- Los marcadores `ICONO:` llevan texto de 12 pt (la skill dice 10 pt, pero fija 12 pt como mínimo absoluto).
- En la diapositiva 9 el bloque se llama "Conteo" (no "CountVectorizer") porque el nombre largo no cabe en el ancho del bloque a 20 pt; el nombre técnico se menciona en las notas.
- El heatmap método × categoría (`figuras/heatmap_metodo_categoria.png`) y la gráfica de latencia (`figuras/latencia.png`) se generaron pero no se usan: el título de la diapositiva 12 es el hallazgo 3 (tipo de consulta), y el heatmap no lo respalda. La latencia de Word2Vec (2.46 ms) se cita en las notas de la 11.
- Las nubes de la diapositiva 7 dimensionan las palabras por frecuencia × proporción propia de la categoría, para resaltar lo característico (se aclara en el pie de la diapositiva).

## Marcadores ICONO pendientes (reemplazar por iconos reales)

- Diapositiva 1: ICONO: lupa sobre un periódico
- Diapositiva 8: ICONO: teclado; ICONO: escoba; ICONO: tabla numérica; ICONO: ángulo; ICONO: podio
- Diapositiva 9: ICONO: contador; ICONO: balanza; ICONO: curva; ICONO: matriz comprimida

---
name: presentacion
description: Extrae estilos y estructura (colores, tipografías, layouts) de una plantilla ejecutiva .pptx y genera con ella la presentación final de resultados del sistema de recuperación BBC, con storytelling. Úsala en la etapa presentacion del pipeline o cuando pidan armar o actualizar las diapositivas.
---

# Presentación ejecutiva

Se califica estrictamente que **no sea genérica**. La presentación se construye **sobre la plantilla elegida por el equipo** (sus layouts, colores y fuentes), nunca desde una presentación en blanco ni mezclando plantillas.

## Requisito previo

`presentacion/plantilla/plantilla.pptx` debe existir (descargada por el equipo de Slidesgo, Canva → exportar a PowerPoint, Envato, etc.). Si no existe, detente y pídela; no inventes una.

## Criterios de diseño (obligatorios)

- **Nada de viñetas.** Donde iría una lista, usa iconos o ilustraciones, cifras grandes, o divide en varias diapositivas.
- **Una idea por diapositiva**: el título es una frase-hallazgo (p. ej. "BM25 encuentra la noticia correcta 9 de cada 10 veces"), no un tema ("Resultados").
- Máximo **60 palabras** por diapositiva sin contar las notas del orador.
- Tipografías: solo las de la plantilla; si la plantilla usa una fuente decorativa poco legible, sustitúyela en el cuerpo por Calibri, Arial o Montserrat.
- Efectos/transiciones: ninguno, salvo que la plantilla los traiga y aporten.
- Números: miles con coma (`2,126`), porcentajes con 2 decimales (`87.35%`).
- **Iconos**: no los generes ni los descargues. Deja un marcador: rectángulo con borde punteado del color de acento y el texto `ICONO: <qué debe representar>` (p. ej. `ICONO: lupa sobre un periódico`). El equipo los reemplaza.

## Paso 1 — Extraer estilos (`src/extraer_estilo.py`)

Con `python-pptx` y lectura del XML del tema (`ppt/theme/theme1.xml` dentro del .pptx, que es un zip):
1. Paleta: `dk1, lt1, dk2, lt2, accent1…accent6` de `<a:clrScheme>` (hex).
2. Fuentes: `<a:majorFont>` (títulos) y `<a:minorFont>` (cuerpo), atributo `latin typeface`.
3. Tamaño de diapositiva (`slide_width`, `slide_height`).
4. Por cada layout: índice, nombre y lista de placeholders (`idx`, tipo, posición, tamaño).
5. De las diapositivas de ejemplo de la plantilla: tamaños de fuente usados en títulos y cuerpo (moda), alineación y márgenes típicos.
6. Guarda todo en `presentacion/estilo.json` y escribe en `presentacion/estilo.md` qué layout usarás para cada tipo de diapositiva: `portada`, `seccion`, `cifra_grande`, `imagen_completa`, `dos_columnas`, `cierre`.

## Paso 2 — Gráficas con la identidad de la plantilla (`src/graficas_presentacion.py`)

Regenera las gráficas clave desde `reports/*.csv` usando **la paleta de `estilo.json`** (accent1…accent5 para las categorías/métodos) y la fuente de cuerpo; fondo transparente, sin bordes, 200 dpi, en `presentacion/figuras/`:
- distribución de categorías, Zipf, Heaps, una wordcloud por categoría (colormap derivado del accent), MAP@10 por método, heatmap método × categoría, latencia.
Que ninguna gráfica tenga más de un mensaje; resalta con accent1 el elemento del que habla el título y deja el resto en gris.

## Paso 3 — Guion (storytelling)

Escribe `presentacion/guion.md` antes de generar nada. Estructura sugerida (12–14 diapositivas):

1. Portada: título del proyecto, equipo, materia, fecha.
2. El problema: encontrar la noticia correcta entre miles (cifra grande: `2,225` noticias).
3. El corpus: 5 categorías, distribución (gráfica).
4. Limpieza: de 2,225 a 2,126 documentos; qué se quitó y por qué (cifra grande + icono).
5. Ley de Zipf: pocas palabras dominan (gráfica + exponente).
6. Ley de Heaps: el vocabulario sigue creciendo (gráfica + β).
7. Wordclouds: cada categoría tiene su "huella" (2–3 nubes).
8. Cómo funciona el buscador: consulta → preprocesamiento → vectorización → coseno/BM25 → ranking (diagrama con marcadores de icono por paso, sin viñetas).
9. Los cuatro métodos en una frase cada uno (cuatro bloques con icono; CountVectorizer, TF-IDF, BM25, SVD).
10. Resultado principal: método ganador (cifra grande de MAP@10).
11. Comparación de métodos (gráfica MAP@10).
12. Dónde falla cada uno (heatmap por categoría o un caso de discrepancia).
13. Demo: una consulta real y su top-3.
14. Conclusión y recomendación (una frase) + siguiente paso.

Usa los 3 hallazgos de `reports/evaluacion.md` como títulos de las diapositivas 10–12. Cada diapositiva lleva en notas del orador el texto que se dirá (40–80 palabras).

## Paso 4 — Generar (`src/generar_presentacion.py`)

1. Abre `plantilla.pptx` con `Presentation()`; elimina sus diapositivas de ejemplo (borrando sus `sldId` de `prs.slides._sldIdLst` y la relación correspondiente) para conservar masters y layouts.
2. Crea cada diapositiva con el layout asignado en `estilo.md`, rellenando **placeholders** (no cajas de texto sueltas) siempre que el layout los tenga.
3. Inserta las gráficas de `presentacion/figuras/` respetando márgenes de la plantilla; nunca deformes la proporción.
4. Escribe las notas del orador desde `guion.md`.
5. Guarda `presentacion/salida/presentacion_final.pptx`.

## Paso 5 — Revisión visual

1. Convierte a imágenes: `soffice --headless --convert-to pdf presentacion/salida/presentacion_final.pptx --outdir presentacion/salida/` y luego `pdftoppm -png -r 60` del PDF.
2. Mira **cada** imagen y revisa: texto que se desborda o se corta, solapamientos, contraste bajo, elementos desalineados, gráficas pixeladas, diapositivas con más de una idea.
3. Corrige y regenera hasta que no haya problemas.
4. Escribe `presentacion/salida/revision_visual.md`: por diapositiva, OK o qué se corrigió, y la lista de marcadores `ICONO:` pendientes para el equipo.

## No hagas

- No uses la plantilla por defecto de python-pptx ni mezcles layouts de otra plantilla.
- No pegues tablas largas: máximo 4 filas × 4 columnas; si hay más, conviértelo en gráfica.

---
name: presentacion
description: Diseña desde cero (sin plantilla) y genera la presentación ejecutiva de resultados de un sistema de recuperación de información con python-pptx - sistema de diseño propio, storytelling, gráficas con la identidad del deck y revisión visual sin depender de LibreOffice. Úsala en la etapa presentacion del pipeline o cuando pidan armar o actualizar las diapositivas.
---

# Presentación ejecutiva (diseño propio, sin plantilla)

Se califica estrictamente que **no sea genérica**. Como no hay plantilla, tú defines un sistema de diseño propio, lo documentas y lo aplicas igual en todas las diapositivas. No uses los layouts por defecto de python-pptx (título + viñetas): todas las diapositivas se construyen sobre el layout en blanco (`prs.slide_layouts[6]`) con formas y cajas de texto posicionadas por ti.

**No se necesita LibreOffice ni poppler.** Si están instalados, se usan como revisión extra (paso 6C); si no, la revisión se hace con las vistas previas propias del paso 5.

## Criterios de diseño (obligatorios)

- **Nada de viñetas.** Donde iría una lista: iconos, cifras grandes, bloques separados o varias diapositivas.
- **Una idea por diapositiva.** El título es una frase-hallazgo ("BM25 encuentra el documento correcto 9 de cada 10 veces"), no un tema ("Resultados").
- Máximo **60 palabras** por diapositiva, sin contar las notas del orador.
- Solo tipografías estándar y legibles. Sin animaciones ni transiciones.
- Números: miles con coma (`12,345`) y porcentajes con 2 decimales (`87.35%`).
- **Iconos**: no los generes ni los descargues. Deja un marcador: un rectángulo redondeado con borde punteado del color de acento y el texto `ICONO: <qué debe representar>` en 10 pt (p. ej. `ICONO: lupa sobre un periódico`). El equipo los reemplaza después.

## Paso 1 — Sistema de diseño (`src/presentacion/diseno.py` + `presentacion/estilo.json`)

Define estas constantes en código y guárdalas también en `presentacion/estilo.json` con las claves `lienzo`, `paleta`, `categorias`, `tipografia` y `layouts` (la validación lo lee):

**Lienzo**: 16:9, `13.333 × 7.5 in`. Márgenes: 0.6 in laterales, 0.5 in arriba y abajo. Retícula de 12 columnas con medianil de 0.2 in; todo se alinea a ella.

**Paleta** (no la cambies sin documentarlo):

| Token | Hex | Uso |
|---|---|---|
| `fondo` | `#F6F4EF` | fondo de todas las diapositivas de contenido |
| `fondo_oscuro` | `#14213D` | portada, separadores de sección y cierre |
| `tinta` | `#1B1F24` | títulos y texto principal |
| `tinta_suave` | `#5C6370` | texto secundario, notas al pie, ejes |
| `acento` | `#E07A1F` | **un solo** elemento destacado por diapositiva (cifra, barra ganadora, palabra clave) |
| `acento_2` | `#2A9D8F` | segundo nivel de énfasis (uso escaso) |
| `neutro` | `#C9CCD1` | todo lo que no es protagonista en gráficas |

Categorías (en gráficas donde todas deben distinguirse): los colores de `presentacion.colores_categorias` en `proyecto.yaml`, con sus nombres para mostrar en `presentacion.categorias_es`. Si faltan, elige colores que contrasten con `fondo` y regístralos ahí.

**Tipografía**: títulos en **Georgia** (negrita), cuerpo en **Calibri**. Escala fija:

| Estilo | Fuente | Tamaño |
|---|---|---|
| Título portada | Georgia bold | 44 pt |
| Título de diapositiva | Georgia bold | 30 pt |
| Cifra grande | Georgia bold | 110 pt, color `acento` |
| Subtítulo / texto de apoyo | Calibri | 20 pt |
| Etiquetas y pie | Calibri | 12 pt, `tinta_suave` |
| Mínimo absoluto | — | 12 pt (si no cabe, divide la diapositiva; nunca reduzcas más) |

**Elementos fijos** en diapositivas de contenido: número de diapositiva abajo a la derecha (12 pt, `tinta_suave`) y nombre corto del proyecto abajo a la izquierda (12 pt). Nada más: sin líneas decorativas bajo el título, sin logos de relleno.

## Paso 2 — Biblioteca de layouts (`src/presentacion/layouts.py`)

Una función por tipo de diapositiva; todas reciben `(prs, datos)` y usan solo los tokens del paso 1:

| Layout | Composición |
|---|---|
| `portada` | Fondo oscuro. Título 44 pt alineado a la izquierda en columnas 1–9, subtítulo debajo, equipo/materia/fecha abajo en 12 pt. Marcador de icono grande en columnas 10–12. |
| `seccion` | Fondo oscuro. Número de sección grande en `acento` + nombre de la sección. |
| `cifra_grande` | Cifra de 110 pt en columnas 1–6, centrada verticalmente; a la derecha (columnas 7–12) una frase de máximo 20 palabras que la explica. |
| `grafica` | Título arriba; gráfica en columnas 1–8; a la derecha (9–12) el mensaje clave en 20 pt (máx. 25 palabras). |
| `grafica_completa` | Título arriba; gráfica a todo el ancho útil; pie de fuente de 12 pt. |
| `bloques` | 2 a 4 bloques en fila, cada uno: marcador de icono + nombre (20 pt bold) + una frase (máx. 15 palabras). Sustituye a cualquier lista. |
| `flujo` | Pasos en fila conectados con flechas (formas `RIGHT_ARROW` en `neutro`); cada paso: marcador de icono + etiqueta corta. El paso clave en `acento`. |
| `demo` | Consulta en una "barra de búsqueda" (rectángulo redondeado con texto en Calibri 22 pt) y debajo el top-3 como tarjetas con rango, categoría y título. |
| `cierre` | Fondo oscuro. Una frase de conclusión y la recomendación. |

Reglas de las funciones: cada caja de texto con `word_wrap=True`, `auto_size` desactivado y márgenes internos de 0.1 in; las imágenes se insertan conservando su proporción (calcula el ancho o el alto que falte). Cada función devuelve, además de la diapositiva, una lista de "cajas" `{tipo, x, y, w, h, texto, tamaño, color}` para la revisión y la vista previa.

## Paso 3 — Gráficas con la identidad del deck (`src/presentacion/graficas.py`)

Regenera las gráficas desde `reports/*.csv` y `reports/*.json`, sin reutilizar los PNG del EDA:
- matplotlib, fuente Calibri si está disponible (si no, `DejaVu Sans`), 200 dpi, fondo transparente.
- Sin marco superior ni derecho, sin cuadrícula salvo líneas horizontales tenues en `neutro`.
- **Una idea por gráfica**: el elemento del que habla el título va en `acento` y todo lo demás en `neutro`.
- Etiquetas directas sobre barras o líneas en vez de leyenda siempre que se pueda.
- Gráficas mínimas: distribución de categorías, Zipf (con recta ajustada), Heaps (con curva ajustada), wordclouds de 2–3 categorías (colormap de un solo tono derivado de su color), MAP@10 por método, heatmap método × categoría, latencia.
- Guarda en `presentacion/figuras/`.

## Paso 4 — Guion (storytelling) → `presentacion/guion.md` y `presentacion/slides.json`

Primero escribe el guion en `guion.md`; después pásalo a `slides.json` (lista de diapositivas con `layout`, `titulo`, campos del layout y `notas`). Estructura (13–14 diapositivas):

1. `portada`: `proyecto.titulo`, `proyecto.equipo`, `proyecto.materia` y la fecha (de `proyecto.yaml`).
2. `cifra_grande`: el problema, encontrar el documento correcto entre los N del corpus (`n_docs` de `reports/eda_raw.json`; llama a los documentos como diga `presentacion.unidad`).
3. `grafica`: el corpus, sus categorías y su distribución.
4. `cifra_grande`: limpieza, cuántos documentos quedaron y por qué (`reports/limpieza.json`).
5. `grafica`: Zipf, pocas palabras dominan (con el exponente).
6. `grafica`: Heaps, el vocabulario sigue creciendo (con β).
7. `bloques`: cada categoría tiene su huella (2–3 wordclouds como bloques).
8. `flujo`: cómo funciona el buscador, consulta → preprocesamiento → vectorización → coseno / BM25 → ranking.
9. `bloques`: los cuatro métodos en una frase cada uno (CountVectorizer, TF-IDF, BM25, SVD).
10. `cifra_grande`: método ganador con su MAP@10.
11. `grafica`: comparación de métodos.
12. `grafica_completa`: dónde falla cada uno (heatmap) o un caso de discrepancia.
13. `demo`: una consulta real y su top-3.
14. `cierre`: conclusión y recomendación.

Usa los 3 hallazgos de `reports/evaluacion.md` como títulos de las diapositivas 10–12. Cada diapositiva lleva notas del orador de 40–80 palabras.

## Paso 5 — Generar el deck y las vistas previas (`src/presentacion/generar.py`)

1. `Presentation()`, ajusta `slide_width`/`slide_height` a 16:9 y crea cada diapositiva desde `slides.json` con su función de layout.
2. Escribe las notas del orador.
3. Guarda `presentacion/salida/presentacion_final.pptx`.
4. **Vista previa propia** (no requiere LibreOffice): con Pillow, dibuja cada diapositiva a 1600 × 900 px a partir de la lista de cajas devuelta por los layouts: fondo, rectángulos, imágenes pegadas en su posición y tamaño, y texto con `ImageFont.truetype` (Georgia/Calibri si se encuentran en el sistema; si no, DejaVu Serif/Sans) usando el mismo ajuste de líneas que el ancho de la caja. Guarda `presentacion/salida/preview/slide_01.png`, … y un `contact_sheet.png` con todas en miniatura.

## Paso 6 — Revisión (obligatoria)

**A. Revisión automática** (`src/presentacion/revisar.py`), sobre el .pptx y las cajas:
- Ninguna forma sale de los márgenes del lienzo.
- No hay cajas de texto que se solapen entre sí.
- El texto cabe: con las métricas de la fuente (Pillow) calcula las líneas necesarias para el ancho de la caja; líneas × tamaño × 1.2 ≤ alto de la caja.
- Ningún texto menor a 12 pt; ninguna diapositiva con más de 60 palabras; ningún párrafo con viñeta o con `level > 0`.
- Contraste de texto contra su fondo ≥ 4.5:1 (fórmula WCAG de luminancia relativa).
- Las imágenes conservan su proporción (diferencia < 1%).
- Máximo un color `acento` "protagonista" por diapositiva (aviso, no error).
Escribe `presentacion/salida/revision_automatica.json` con la forma `{"errores": <int>, "avisos": <int>, "detalle": [...]}` (la validación exige `errores == 0`). Si algo falla, corrige el layout o divide la diapositiva y regenera.

**B. Revisión visual con las vistas previas**: abre y **mira cada** `preview/slide_XX.png` y busca desbalance, huecos grandes, alineaciones que no sigan la retícula, gráficas ilegibles a tamaño de proyección y diapositivas con más de una idea. Corrige y regenera.

**C. Opcional, si existe `soffice`** (`which soffice`): convierte a PDF con `soffice --headless --convert-to pdf` y, si existe `pdftoppm`, rasteriza a 60 dpi y compara con las vistas previas. Si no existen, no los instales: anótalo en el informe y sigue.

**D. Informe**: escribe `presentacion/salida/revision_visual.md` con, por diapositiva, OK o qué se corrigió; la lista de marcadores `ICONO:` pendientes para el equipo; y la nota: "Revisar en PowerPoint/Keynote/Google Slides antes de presentar: la vista previa es aproximada".

## No hagas

- No uses layouts de python-pptx con placeholders de viñetas ni el tema por defecto "Office" tal cual.
- No pegues tablas de más de 4 filas × 4 columnas; conviértelas en gráfica.
- No uses más de 2 colores de énfasis en una diapositiva.

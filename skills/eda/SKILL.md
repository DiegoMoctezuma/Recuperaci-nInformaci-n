---
name: eda
description: Análisis exploratorio de un corpus de textos en dos modos, que además decide los parámetros de las etapas siguientes a partir de lo que encuentra. Modo "raw" (antes de limpiar) - categorías, longitudes, duplicados, idioma y caracteres. Modo "corpus" (después de limpiar) - vocabulario, ley de Zipf, ley de Heaps y wordclouds. Úsala en las etapas eda_raw y eda_corpus del pipeline.
---

# Análisis exploratorio (EDA)

Primero identifica el modo: la etapa `eda_raw` usa **modo raw**; la etapa `eda_corpus` usa **modo corpus**. Todo el código va en `src/eda.py` con un argumento: `python src/eda.py --modo raw` o `--modo corpus`.

El EDA no solo describe: **decide**. Respeta lo que esté fijado en `proyecto.yaml`; lo que esté en `auto` lo decides con las reglas de cada modo, lo escribes de vuelta y lo registras en `decisiones` con su razón (ver la skill `orquestador`).

Reglas de formato para reportes y gráficas:
- Números con separador de miles (`12,345`), porcentajes con 2 decimales (`22.97%`).
- Gráficas con matplotlib, 150 dpi, PNG, título y ejes rotulados, guardadas en `reports/figuras/`.
- Paleta fija por categoría: `eda.paleta_categorias`. Si es `auto`, asigna los colores de `tab10` (o `tab20` si hay más de 10 categorías) en orden alfabético de categoría y regístrala. Exponla en `src/estilo_graficas.py`, leída de `proyecto.yaml`.
- Si no hay categorías (`datos.columna_categoria: null`), omite todo lo que sea "por categoría" y dilo en el reporte.

---

## Modo raw (entrada: `datos.ruta_raw`)

### Mide

1. Conteo y porcentaje por categoría → `reports/figuras/raw_categorias.png` (barras). Si hay más de 20 categorías, grafica las 20 mayores y agrupa el resto en "otras".
2. Nulos por columna y documentos con texto vacío.
3. Duplicados exactos en el texto (`duplicated(keep="first")`), su distribución por categoría y si algún grupo tiene categorías distintas.
4. Longitud en palabras y en caracteres: media, mediana, min, max, p1, p25, p75, p99, global y por categoría → `reports/figuras/raw_longitudes.png` (boxplot por categoría, o histograma si no hay categorías).
5. Caracteres: % de documentos con dígitos, con mayúsculas, con cada símbolo frecuente (los 10 caracteres no alfanuméricos más comunes) y los 10 caracteres no ASCII más frecuentes.
6. Idioma: para cada documento, la proporción de palabras que son stopwords de spaCy en cada idioma candidato (`en`, `es`, `fr`, `pt`, `de`, `it`); el idioma del documento es el de mayor proporción. Reporta el % de documentos por idioma.

### Decide según los datos (si está en `auto`)

| Clave | Regla |
|---|---|
| `datos.idioma` | El idioma de ≥ 80% de los documentos. Si ninguno llega a 80%, detente y pregunta (corpus mezclado). |
| `datos.duplicados_esperados` | El número de duplicados exactos encontrado. |
| `limpieza.simbolos_a_espacio` | Los símbolos que aparecen pegados entre letras (`-`, `/`, `_`, `.` dentro de palabra) y los de moneda: se cambian por espacio para no fundir palabras. |
| `limpieza.conservar_numeros` | `false` salvo que los números sean el contenido (más de 20% de los tokens son números, p. ej. reportes financieros); entonces `true` y explícalo. |
| `limpieza.min_tokens_documento` | `20` si la mediana del texto es ≥ 100 palabras; `5` si está entre 20 y 100; `3` si es menor (textos cortos como reseñas o tuits). |
| `limpieza.palabras_titulo` | Si hay `columna_titulo`, no aplica (`null`). Si no, `8` palabras, o el texto completo si la mediana es menor de 15 palabras. |
| `evaluacion.modo` | `juicios` si existen juicios de relevancia; `categoria` si hay categorías; `item_conocido` si no hay categorías. |
| `eda.zipf.rango_ajuste`, `eda.heaps.paso_tokens` | Se deciden en el modo corpus. |

Si las longitudes son extremas, escríbelo como advertencia (no se corrige aquí): mediana > 2,000 palabras (los documentos largos dominan BM25 y conviene revisar `b`), o categorías desbalanceadas (la mayor más de 5 veces la menor: la evaluación debe reportar también el promedio por categoría).

### Salidas

- `reports/eda_raw.md` con secciones: Resumen, Categorías, Calidad (nulos/duplicados), Longitudes, Idioma y caracteres, **Decisiones tomadas** (tabla clave → valor → razón) y Advertencias.
- `reports/eda_raw.json` con al menos `n_docs`, `n_duplicados`, `conteo_categorias` (vacío si no hay), `longitud_media`, `idioma`, `pct_idioma`.

---

## Modo corpus (entrada: `data/processed/corpus_clean.csv`, columna `tokens_lemma`)

Los tokens están guardados como texto separado por espacios; usa `.str.split()`.

### Decide según los datos (si está en `auto`)

| Clave | Regla |
|---|---|
| `eda.zipf.rango_ajuste` | `[1, min(1000, V // 10)]`, con V el tamaño del vocabulario. |
| `eda.heaps.paso_tokens` | `max(500, N // 100)` redondeado a la centena, con N los tokens totales (unos 100 puntos de curva). |
| Categorías a graficar | Todas si son ≤ 12; si son más, las 12 con más documentos. |

### Mide

1. **Vocabulario**: N tokens, V tipos, hapax legomena (cantidad y % del vocabulario), top 30 global y top 15 por categoría → `reports/vocabulario_top.csv`, vocabulario por categoría y términos exclusivos de cada categoría (top 10).
2. **Ley de Zipf**: frecuencias ordenadas, gráfica log-log rango vs. frecuencia → `reports/figuras/zipf.png`; ajuste `log f = log C − s·log r` con `numpy.polyfit` en `eda.zipf.rango_ajuste`; reporta `s` y R² y dibuja la recta. Si `s` está fuera de [0.8, 1.2], repite el ajuste sobre `text_norm` (con stopwords) e informa ambos: quitar stopwords baja el exponente.
3. **Ley de Heaps**: documentos en orden aleatorio (`proyecto.semilla`), un punto (n tokens, V tipos) cada `eda.heaps.paso_tokens`; ajuste `V = K·n^β` en log-log; reporta `K`, `β`, R² y grafica observada y ajustada → `reports/figuras/heaps.png`. Interpreta β: lo típico en lenguaje natural es 0.4–0.7; si sale fuera, menciónalo.
4. **Wordclouds**: una global y una por categoría graficada, con `wordcloud.WordCloud(width=1600, height=900, background_color="white", random_state=<semilla>, max_words=150)` y `generate_from_frequencies` → `reports/figuras/wordcloud_global.png` y `wordcloud_<categoria>.png` (nombre de archivo seguro: minúsculas, sin espacios ni acentos).
5. **Lema vs. stem**: tamaño del vocabulario con `tokens_lemma` y con `tokens_stem`; una línea de conclusión.

### Salidas

- `reports/eda_corpus.md` con secciones: Vocabulario, Zipf (con `s` y R²), Heaps (con `K`, `β`, R²), Wordclouds (enlaces a las imágenes), Lema vs. stem, Decisiones tomadas, Conclusiones para la indexación (p. ej. qué % del vocabulario quitaría `min_df=2`).
- `reports/eda_corpus.json` con `N`, `V`, `hapax`, `zipf_s`, `zipf_r2`, `heaps_K`, `heaps_beta`, `heaps_r2`.

## No hagas

- No modifiques los archivos de `data/`.
- No uses seaborn ni estilos que cambien la paleta fija.
- No cambies un valor de `proyecto.yaml` que el usuario fijó (sin `auto`).

---
name: eda
description: Análisis exploratorio del corpus BBC en dos modos. Modo "raw" (antes de limpiar) - distribución de categorías, longitudes, nulos y duplicados. Modo "corpus" (después de limpiar) - vocabulario, ley de Zipf, ley de Heaps y wordclouds. Úsala en las etapas eda_raw y eda_corpus del pipeline.
---

# Análisis exploratorio (EDA)

Primero identifica el modo: la etapa `eda_raw` usa **modo raw**; la etapa `eda_corpus` usa **modo corpus**. Todo el código va en `src/eda.py` con un argumento: `python src/eda.py --modo raw` o `--modo corpus`.

Reglas de formato para reportes y gráficas:
- Números con separador de miles (`2,126`), porcentajes con 2 decimales (`22.97%`).
- Gráficas con matplotlib, 150 dpi, PNG, título y ejes rotulados, guardadas en `reports/figuras/`.
- Paleta fija por categoría (úsala igual en todo el proyecto y guárdala en `src/estilo_graficas.py`):
  `business #1f77b4, entertainment #ff7f0e, politics #2ca02c, sport #d62728, tech #9467bd`.

---

## Modo raw (entrada: `data/raw/bbc-text.csv`)

1. Carga el CSV con pandas.
2. Calcula y guarda:
   - Conteo y porcentaje por categoría → `reports/figuras/raw_categorias.png` (barras).
   - Nulos por columna.
   - Duplicados exactos en `text` (se esperan 99) y su distribución por categoría.
   - Longitud en palabras (`text.str.split().str.len()`): media, mediana, min, max, p25, p75, global y por categoría → `reports/figuras/raw_longitudes.png` (boxplot por categoría).
   - Longitud en caracteres (misma descripción).
   - Presencia de caracteres no alfabéticos: % de documentos con dígitos, con símbolos (`£`, `$`, `%`, `-`).
3. Escribe `reports/eda_raw.md` con secciones: Resumen, Categorías, Calidad (nulos/duplicados), Longitudes, Hallazgos que afectan la limpieza (lista de decisiones sugeridas, p. ej. "quitar 99 duplicados", "conservar números" o "quitarlos").
4. Guarda las métricas clave en `reports/eda_raw.json` (`n_docs`, `n_duplicados`, `conteo_categorias`, `longitud_media`) para que la validación las lea.

---

## Modo corpus (entrada: `data/processed/corpus_clean.csv`, columna `tokens_lemma`)

Los tokens están guardados como texto separado por espacios; usa `.str.split()`.

1. **Vocabulario**
   - Tamaño total del corpus (N tokens) y del vocabulario (V tipos).
   - Hapax legomena (palabras con frecuencia 1): cantidad y % del vocabulario.
   - Top 30 palabras globales y top 15 por categoría → `reports/vocabulario_top.csv`.
   - Vocabulario por categoría y palabras exclusivas de cada categoría (top 10).
2. **Ley de Zipf**
   - Ordena frecuencias de mayor a menor; rango r = 1..V.
   - Gráfica log-log rango vs. frecuencia → `reports/figuras/zipf.png`.
   - Ajusta `log f = log C − s·log r` con `numpy.polyfit` sobre los rangos 1 a 1,000; reporta `s` y R². Dibuja la recta ajustada en la misma gráfica.
3. **Ley de Heaps**
   - Recorre los documentos en orden aleatorio (semilla 42) acumulando tokens; cada 5,000 tokens registra (n tokens, V tipos).
   - Ajusta `V = K·n^β` en log-log con `numpy.polyfit`; reporta `K`, `β` y R².
   - Gráfica de la curva observada y la ajustada → `reports/figuras/heaps.png`.
   - Interpretación esperada: β entre 0.4 y 0.7 para texto en inglés; si sale fuera, menciónalo.
4. **Wordclouds**
   - Una global y una por categoría (6 imágenes) con `wordcloud.WordCloud(width=1600, height=900, background_color="white", random_state=42, max_words=150)`, usando frecuencias (`generate_from_frequencies`), no texto crudo.
   - Guarda en `reports/figuras/wordcloud_<categoria>.png` y `wordcloud_global.png`.
5. **Comparación lema vs. stem**: tamaño del vocabulario con `tokens_lemma` y con `tokens_stem`; una línea de conclusión.
6. Escribe `reports/eda_corpus.md` con secciones: Vocabulario, Zipf (con `s` y R²), Heaps (con `K`, `β`, R²), Wordclouds (enlaces a las imágenes), Lema vs. stem, Conclusiones para la indexación.
7. Guarda `reports/eda_corpus.json` con `N`, `V`, `hapax`, `zipf_s`, `zipf_r2`, `heaps_K`, `heaps_beta`, `heaps_r2`.

## No hagas

- No modifiques los archivos de `data/`.
- No uses seaborn ni estilos que cambien la paleta fija.

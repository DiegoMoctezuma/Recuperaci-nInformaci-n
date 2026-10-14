---
name: eda
description: Análisis exploratorio de un corpus de textos con categoría, en dos modos. Modo "raw" (antes de limpiar) - distribución de categorías, longitudes, nulos y duplicados. Modo "corpus" (después de limpiar) - vocabulario, ley de Zipf, ley de Heaps y wordclouds. Úsala en las etapas eda_raw y eda_corpus del pipeline.
---

# Análisis exploratorio (EDA)

Primero identifica el modo: la etapa `eda_raw` usa **modo raw**; la etapa `eda_corpus` usa **modo corpus**. Todo el código va en `src/eda.py` con un argumento: `python src/eda.py --modo raw` o `--modo corpus`. Las rutas, columnas, categorías y parámetros salen de `proyecto.yaml` (secciones `datos` y `eda`).

Reglas de formato para reportes y gráficas:
- Números con separador de miles (`12,345`), porcentajes con 2 decimales (`22.97%`).
- Gráficas con matplotlib, 150 dpi, PNG, título y ejes rotulados, guardadas en `reports/figuras/`.
- Paleta fija por categoría: la de `eda.paleta_categorias`. Úsala igual en todo el proyecto y exponla en `src/estilo_graficas.py` (leída de `proyecto.yaml`, no copiada). Si falta, asigna una paleta categórica de matplotlib en orden alfabético de categoría y regístrala en `proyecto.yaml`.

---

## Modo raw (entrada: `datos.ruta_raw`)

1. Carga el CSV con pandas; trabaja con `datos.columna_texto` y `datos.columna_categoria`.
2. Calcula y guarda:
   - Conteo y porcentaje por categoría → `reports/figuras/raw_categorias.png` (barras).
   - Nulos por columna.
   - Duplicados exactos en el texto (`duplicated(keep="first")`; se esperan `datos.duplicados_esperados`) y su distribución por categoría. Comprueba si algún grupo de duplicados tiene categorías distintas.
   - Longitud en palabras (`str.split().str.len()`): media, mediana, min, max, p25, p75, global y por categoría → `reports/figuras/raw_longitudes.png` (boxplot por categoría).
   - Longitud en caracteres (misma descripción).
   - Presencia de caracteres no alfabéticos: % de documentos con dígitos y con cada símbolo de `eda.simbolos_a_contar`; % con mayúsculas; caracteres no ASCII más frecuentes.
3. Escribe `reports/eda_raw.md` con secciones: Resumen, Categorías, Calidad (nulos/duplicados), Longitudes, Hallazgos que afectan la limpieza (lista de decisiones sugeridas, p. ej. "quitar N duplicados", "conservar números" o "quitarlos").
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
   - Ajusta `log f = log C − s·log r` con `numpy.polyfit` sobre los rangos de `eda.zipf.rango_ajuste`; reporta `s` y R². Dibuja la recta ajustada en la misma gráfica.
   - Si `s` queda lejos de 1, repite el ajuste sobre `text_norm` (con stopwords) e informa ambos valores: quitar stopwords baja el exponente.
3. **Ley de Heaps**
   - Recorre los documentos en orden aleatorio (`proyecto.semilla`) acumulando tokens; cada `eda.heaps.paso_tokens` tokens registra (n tokens, V tipos).
   - Ajusta `V = K·n^β` en log-log con `numpy.polyfit`; reporta `K`, `β` y R².
   - Gráfica de la curva observada y la ajustada → `reports/figuras/heaps.png`.
   - Interpretación: compara β con `eda.heaps.beta_tipico` (rango típico para el idioma del corpus); si sale fuera, menciónalo.
4. **Wordclouds**
   - Una global y una por categoría con `wordcloud.WordCloud(width=1600, height=900, background_color="white", random_state=<semilla>, max_words=150)`, usando frecuencias (`generate_from_frequencies`), no texto crudo.
   - Guarda en `reports/figuras/wordcloud_<categoria>.png` y `wordcloud_global.png`.
5. **Comparación lema vs. stem**: tamaño del vocabulario con `tokens_lemma` y con `tokens_stem`; una línea de conclusión.
6. Escribe `reports/eda_corpus.md` con secciones: Vocabulario, Zipf (con `s` y R²), Heaps (con `K`, `β`, R²), Wordclouds (enlaces a las imágenes), Lema vs. stem, Conclusiones para la indexación.
7. Guarda `reports/eda_corpus.json` con `N`, `V`, `hapax`, `zipf_s`, `zipf_r2`, `heaps_K`, `heaps_beta`, `heaps_r2`.

## No hagas

- No modifiques los archivos de `data/`.
- No uses seaborn ni estilos que cambien la paleta fija.

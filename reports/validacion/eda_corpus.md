# Validación eda_corpus

- Fecha: 2026-10-11
- Resultado: **PASS**
- Comando: `conda run -n bbc-ir python src/validar.py --etapa eda_corpus` (código de salida 0)

## Verificaciones del checklist

| id | descripción | resultado | detalle |
|---|---|---|---|
| C1 | reporte EDA corpus | PASS | reports/eda_corpus.md existe |
| C2 | exponente de Zipf plausible | PASS | zipf_s = 0.6088 (rango [0.6, 1.5]) |
| C3 | beta de Heaps plausible | PASS | heaps_beta = 0.5387 (rango [0.3, 0.8]) |
| C4 | buen ajuste de Heaps (no bloqueante) | PASS | heaps_r2 = 0.9976 (rango [0.9, 1.0]) |
| C5 | gráfica Zipf | PASS | reports/figuras/zipf.png existe |
| C6 | gráfica Heaps | PASS | reports/figuras/heaps.png existe |
| C7 | 6 wordclouds | PASS | expr -> True |

## Revisión cualitativa (verificaciones ejecutadas)

| Punto | Resultado | Evidencia |
|---|---|---|
| Recalculo independiente (Counter sobre corpus_clean.csv) | sí, sin discrepancias | N = 385,689; V = 24,971; hapax = 9,980 (39.97%); V con tokens_stem = 21,127 (N_stem 394,426); top 30 global idéntico en JSON, MD y CSV |
| vocabulario_top.csv | sí | 30 filas global + 15 por cada una de las 5 categorías; top 15 por categoría coincide con el recálculo; vocabulario, tokens y términos exclusivos (n y top 10) coinciden en business y politics |
| Zipf | sí | polyfit de log f vs. log r, rangos 1 a 1,000: s = 0.608833, R² = 0.946898, C = 6,751.38; JSON: 0.608833 / 0.946898 (diferencia < 1e-12). El valor bajo es consecuencia del rango de ajuste fijado por la skill (con rango 1..100 s = 0.34, 1..2,000 s = 0.78), no un error de método |
| Heaps | sí | src/eda.py baraja con `np.random.RandomState(42).permutation` y registra cada 5,000 tokens (77 puntos). Replicando esa forma: K = 25.2502, β = 0.538679, R² = 0.997566 (igual al JSON). Sensibilidad al barajado: default_rng(42) β = 0.5427, random.Random(42).shuffle β = 0.5512; todos dentro de 0.4-0.7 |
| WordCloud en código | sí | width=1600, height=900, background_color="white", random_state=42, max_words=150, `generate_from_frequencies` |
| Tamaño de imágenes | sí | 6 wordclouds 1600x900; zipf.png y heaps.png 1200x825 (150 dpi) |
| Figuras (vistas) | sí | zipf: título, ejes rotulados, puntos y recta ajustada con leyenda (s, R²), marca en rango 1,000; heaps: título, ejes, curva observada y ajustada con K, β, R²; wordclouds global, sport y tech legibles |
| Sin seaborn | sí | `grep seaborn|sns src/` sin resultados |
| Secciones del .md | sí | Vocabulario, Zipf (s y R²), Heaps (K, β, R²), Wordclouds, Lema vs. stem, Conclusiones para la indexación |
| Enlaces del .md | sí | 14 enlaces (zipf, heaps, 6 vínculos de wordcloud y 6 imágenes incrustadas) resuelven a archivos existentes relativos a reports/ |
| .md coincide con .json | sí | mismas cifras |
| Formato | sí | miles con coma, porcentajes con 2 decimales; sin enteros de 4+ dígitos sin separador (solo decimales de s, R², β) |
| Determinismo | sí | re-ejecutar `src/eda.py --modo corpus`: MD5 idéntico de JSON, MD, CSV y las 8 figuras |
| No regresión | sí | `src/eda.py --modo raw` código 0; `validar.py --etapa eda_raw` PASS; reports/validacion/eda_raw.json restaurado a su versión original |

## Advertencias (no bloqueantes)

1. Wordclouds con el colormap por defecto de WordCloud (viridis) y no con la paleta por categoría; la skill no lo exige.
2. Artefactos heredados de la limpieza en vocabulario y nubes: `yearold`, `didn`, `don`, `wale`, `kilroysilk`, `ebber`, `torie`.
3. En Heaps no se registra el último tramo < 5,000 tokens (según la letra de la skill).
4. Zipf s = 0.609 queda cerca del mínimo 0.6 del checklist: es el resultado correcto del ajuste en rangos 1-1,000 sobre un corpus sin stopwords (aplana la cabeza de la distribución); el ajuste es mediocre en la cabeza (R² = 0.947), visible en zipf.png.
5. Wordclouds sin título (la skill solo exige título en las gráficas matplotlib).
6. El barajado de Heaps usa RandomState(42) (legado de numpy); equivalente en semilla a lo pedido, aunque difiere de default_rng.

# Validación eda_raw

- Fecha: 2026-10-11
- Resultado: **PASS**
- Comando: `conda run -n bbc-ir python src/validar.py --etapa eda_raw` (código de salida 0)

## Verificaciones del checklist

| id | descripción | resultado | detalle |
|---|---|---|---|
| E1 | reporte EDA raw | PASS | reports/eda_raw.md existe |
| E2 | detectó los 99 duplicados | PASS | n_duplicados = 99 (rango [99, 99]) |
| E3 | gráfica de categorías | PASS | reports/figuras/raw_categorias.png existe |
| E4 | gráfica de longitudes | PASS | reports/figuras/raw_longitudes.png existe |

## Revisión cualitativa (verificaciones ejecutadas)

| Punto | Resultado | Evidencia |
|---|---|---|
| `python src/eda.py --modo raw` corre desde la raíz sin pasos manuales | sí | código 0; salida `n_docs=2,225 n_duplicados=99 longitud_media=390.30` |
| Reproducibilidad | sí | tras re-ejecutar, MD5 idéntico de eda_raw.json, eda_raw.md y ambos PNG (no cambió ninguna salida) |
| Recalculo independiente con pandas desde el CSV | sí, sin discrepancias | conteo y % por categoría; 99 duplicados (sport 7, business 7, politics 14, entertainment 17, tech 54; 198 filas en 99 grupos); media/mediana/min/max/p25/p75 en palabras y en caracteres, global y por categoría (diferencia < 1e-9); % con dígitos 95.10% (por categoría coincide); `£` 29.08%, `$` 21.48%, `%` 28.31%, `-` 94.56%, alguno 96.58%; mayúsculas 0.00% |
| .md coincide con .json | sí | mismas cifras, redondeadas a 2 decimales |
| Secciones del .md | sí | Resumen, Categorías, Calidad (nulos y duplicados), Longitudes, Hallazgos que afectan la limpieza |
| Afirmaciones cualitativas de Hallazgos | sí | sin comas, comillas ni apóstrofos (0.00%); doble espacio en 100% de los docs; 97.30% termina en punto |
| Figuras | sí | ambas 1200x750 px, 150 dpi, título, ejes rotulados y legibles; barras con etiquetas de conteo y %; boxplot por categoría |
| Paleta fija | sí | src/estilo_graficas.py define business #1f77b4, entertainment #ff7f0e, politics #2ca02c, sport #d62728, tech #9467bd; los colores se ven en ambas figuras |
| Formato | sí | miles con coma (2,225; 4,492; eje Y 4,000), porcentajes con 2 decimales |
| Sin seaborn | sí | `grep seaborn src/` sin resultados |
| No modifica data/ | sí | `git status data` limpio; SHA-256 del CSV coincide con el .sha256 |
| `--modo corpus` | stub | `NotImplementedError` explícito; acordado, se implementa en eda_corpus (no es FAIL) |

## Advertencias (menores, no bloqueantes)

1. En el boxplot las cajas usan `alpha=0.8`, por lo que el tono visible es ligeramente más claro que el hex exacto de la paleta. Las barras sí usan el color exacto.
2. El `--modo corpus` es un stub (acordado). El SKILL.md de eda lo requiere en la etapa eda_corpus.
3. Los reports/eda_raw.* y reports/figuras/, src/eda.py y src/estilo_graficas.py aún no están versionados en git (untracked al validar).

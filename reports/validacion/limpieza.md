# Validación limpieza

- Fecha: 2026-10-11
- Resultado: **PASS** (con advertencias)
- Comando: `conda run -n bbc-ir python src/validar.py --etapa limpieza` (código de salida 0)

## Verificaciones del checklist

| id | descripción | resultado | detalle |
|---|---|---|---|
| L1 | corpus limpio | PASS | data/processed/corpus_clean.csv existe |
| L2 | duplicados quitados (<= 2,126) | PASS | 2,126 filas (rango [2,050, 2,126]) |
| L3 | columnas en orden | PASS | doc_id, category, titulo, text_original, text_norm, tokens_lemma, tokens_stem, n_tokens |
| L4 | sin nulos | PASS | sin nulos en doc_id, category, tokens_lemma |
| L5 | sin textos duplicados | PASS | 0 duplicados en text_original |
| L6 | doc_id único | PASS | 0 duplicados |
| L7 | sin dígitos, mayúsculas ni stopwords comunes | PASS | expr -> True |
| L8 | preprocesar() reutilizable (no bloqueante) | PASS | `preprocesar('The Markets were FALLING in 2005!') == ['market','fall']` |
| L9 | reporte de limpieza | PASS | reports/limpieza.md existe |

## Revisión independiente

1. **src/preprocesamiento.py vs reglas exactas**: cumple. 5 funciones con las firmas pedidas; `normalizar` (minúsculas, £/$ a espacio, `\d+` fuera, solo a-z/apóstrofo/espacio, quita `'s` y apóstrofos sueltos, colapsa espacios, strip); `tokenizar` (split, len >= 3, STOP_WORDS de spaCy + `STOPWORDS_EXTRA` con exactamente las 12 palabras); `lematizar` (en_core_web_sm cargado una vez a nivel de módulo, `disable=["parser","ner"]`, `token.lemma_`, refiltra stopwords y < 3); `stemizar` (PorterStemmer); `nlp.pipe(..., batch_size=64)` para el corpus. Pipes activos: tok2vec, tagger, attribute_ruler, lemmatizer.
2. **src/limpieza.py vs skill**: cumple. `drop_duplicates(subset="text", keep="first")`, descarte < 20 tokens, doc_id `doc_0000`…, titulo = primeras 8 palabras del original, columnas y orden correctos, no escribe en data/raw/.
3. **Recalculo con pandas**: 2,126 filas = dedup del CSV crudo; doc_id consecutivo doc_0000..doc_2125; `titulo` == primeras 8 palabras de `text_original` (todas); `n_tokens == len(tokens_lemma.split())` (todas); 0 NaN y 0 tokens vacíos; `text_original` y `category` coinciden con el CSV deduplicado en el mismo orden; min n_tokens = 40 (0 descartados cortos, coherente); `text_norm` solo [a-z ]; `tokens_lemma` solo [a-z ]. limpieza.json: n_antes 2,225, n_despues 2,126, duplicados 99, descartados_cortos 0, tokens_promedio 390.45 / 181.42, vocabulario 24,971 / 21,127, todos recalculados sin discrepancia; limpieza.md coincide con el JSON. SHA-256 de data/raw/bbc-text.csv coincide con bbc-text.sha256.
4. **Consistencia preprocesar vs corpus**: muestra de 30 docs (random.seed(42) y también numpy RandomState(42)): lemma 30/30 (100.00%), stem 30/30 (100.00%). Comprobación ampliada: `preprocesar_lote` sobre los 2,126 docs reproduce `tokens_lemma` y `tokens_stem` con 0 diferencias; `preprocesar` individual sobre los primeros 400 docs, 0 diferencias; `normalizar` sobre todos, 0 diferencias. No hay divergencia lote vs individual: no contradice "una sola función".
5. **reports/limpieza.md**: contiene docs antes/después, duplicados, descartados por cortos, tokens promedio antes/después, 3 ejemplos (original -> tokens_lemma, recortados a 30 palabras) y decisiones con su porqué. Ver advertencia 1 sobre formato.

## Advertencias (no bloqueantes)

1. **Formato de miles en reports/limpieza.md**: las cifras enteras aparecen sin separador (`2225`, `2126`, `24971 / 21127`) y no con coma (`2,225`). La skill de limpieza no exige formato, por lo que no es FAIL; sí contradice la convención del proyecto (`2,126`) y la revisión de formato de validacion-calidad. Conviene corregirlo en el reintento o en una pasada posterior (`f"{n:,}"` en src/limpieza.py). No hay porcentajes en el reporte.
2. **Decisión (i), guiones eliminados sin espacio** (`high-definition` -> `highdefinition`, `e-mail` -> `email`): aplica la letra literal de la skill ("elimina todo lo que no sea a-z, apóstrofo o espacio"); documentada en el reporte. Consecuencia: crea tokens fusionados que no coinciden con las consultas del usuario ("high definition") y 94.56% de los docs tienen guion (según eda_raw). Consistente entre corpus y consultas. Se acepta; si se quisiera sustituir por espacio hay que decidirlo explícitamente en la skill.
3. **Decisión (ii), `tokens_stem` calculado sobre tokens filtrados sin lematizar**: la skill no precisa la fuente; es coherente con "tokens stemizados" y está documentado. Vocabulario stem (21,127) < lemma (24,971).
4. **Decisión (iii), `preprocesar_lote` auxiliar**: no contradice la skill (que pide `nlp.pipe` para el corpus); verificado que da idéntico resultado a `preprocesar`.
5. **Lematización sobre tokens ya filtrados y unidos por espacio** (sin contexto sintáctico) y filtro extra `isalpha()` tras lematizar: no está en la skill pero es inocuo (los lemas ya son a-z) y está documentado. Calidad de lemas algo menor (p. ej. "rings" aparece como "ring" y "rings" en un mismo doc).
6. `validar.py` emite un UserWarning de pandas (regex con grupos de captura en L7). Es del script, no de la etapa; no impide validar.
7. Archivos de la etapa (src/limpieza.py, src/preprocesamiento.py, corpus_clean.csv, reports/limpieza.*) aún sin versionar en git al validar. No se re-ejecutó limpieza.py (no se sobrescribió nada); la reproducibilidad se comprobó recomputando en memoria y comparando contra el CSV.

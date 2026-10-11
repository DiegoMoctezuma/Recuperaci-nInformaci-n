---
name: limpieza
description: Limpia, normaliza, tokeniza y lematiza/stemiza el corpus BBC, y expone una función reutilizable de preprocesamiento para documentos nuevos y consultas. Úsala en la etapa limpieza del pipeline o cuando cambie el preprocesamiento.
---

# Limpieza, normalización y tokenización

El preprocesamiento debe ser **una sola función** que se use igual para el corpus, para noticias nuevas (ingesta) y para las consultas. Si la consulta se procesa distinto que el corpus, la recuperación falla.

## Pasos

1. Crea `src/preprocesamiento.py` con:

   ```python
   def normalizar(texto: str) -> str
   def tokenizar(texto: str) -> list[str]
   def lematizar(tokens: list[str]) -> list[str]
   def stemizar(tokens: list[str]) -> list[str]
   def preprocesar(texto: str, modo: str = "lemma") -> list[str]   # modo: "lemma" | "stem"
   ```

   Reglas exactas:
   - `normalizar`: minúsculas; reemplaza `£` y `$` por espacio; elimina dígitos (`\d+`); elimina todo lo que no sea letra a-z, apóstrofo o espacio; quita apóstrofos sueltos y la terminación `'s`; colapsa espacios múltiples; `strip()`.
   - `tokenizar`: `texto.split()`; descarta tokens de longitud < 3; descarta stopwords de `spacy.lang.en.stop_words.STOP_WORDS` **más** esta lista propia: `["said", "mr", "mrs", "ms", "also", "would", "could", "year", "years", "new", "one", "two"]`. Guarda la lista propia como constante `STOPWORDS_EXTRA` para que sea visible.
   - `lematizar`: spaCy `en_core_web_sm` cargado **una vez** a nivel de módulo con `disable=["parser", "ner"]`; usa `token.lemma_`; vuelve a quitar stopwords y tokens < 3 después de lematizar.
   - `stemizar`: `nltk.stem.PorterStemmer`.
   - Para el corpus completo usa `nlp.pipe(textos, batch_size=64)` (no un `nlp()` por documento).

2. Crea `src/limpieza.py` que:
   1. Carga `data/raw/bbc-text.csv`.
   2. Elimina duplicados exactos de `text` con `drop_duplicates(subset="text", keep="first")`. Se esperan **2,126** documentos tras esto.
   3. Elimina documentos que queden con menos de 20 tokens tras preprocesar (registra cuántos).
   4. Asigna `doc_id` = `"doc_0000"`, `"doc_0001"`, … en el orden resultante.
   5. Extrae `titulo` = primeras 8 palabras del texto original (el corpus no separa título y cuerpo; esto es solo para mostrar resultados).
   6. Genera las columnas:
      - `text_original` (sin cambios)
      - `text_norm` (salida de `normalizar`)
      - `tokens_lemma` (tokens lematizados unidos por espacio)
      - `tokens_stem` (tokens stemizados unidos por espacio)
      - `n_tokens` (len de `tokens_lemma`)
   7. Guarda `data/processed/corpus_clean.csv` con columnas en este orden: `doc_id, category, titulo, text_original, text_norm, tokens_lemma, tokens_stem, n_tokens`.
3. Ejecuta `python src/limpieza.py`.
4. Escribe `reports/limpieza.md` con: documentos antes/después, duplicados eliminados, documentos descartados por cortos, tokens promedio antes y después, 3 ejemplos (texto original → tokens_lemma, recortados a 30 palabras), decisiones tomadas y por qué.
5. Guarda `reports/limpieza.json` con `n_antes`, `n_despues`, `duplicados`, `descartados_cortos`, `tokens_promedio`.

## Representación por defecto

Todas las etapas siguientes usan `tokens_lemma`. `tokens_stem` se usa solo para la comparación en EDA y, si sobra tiempo, como variante en evaluación.

## No hagas

- No sobrescribas `data/raw/`.
- No uses otra lista de stopwords sin documentarlo en `reports/limpieza.md`.

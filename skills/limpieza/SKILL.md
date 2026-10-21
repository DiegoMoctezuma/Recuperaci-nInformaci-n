---
name: limpieza
description: Limpia, normaliza, tokeniza y lematiza/stemiza un corpus de textos con categoría, y expone una función reutilizable de preprocesamiento para documentos nuevos y consultas. Úsala en la etapa limpieza del pipeline o cuando cambie el preprocesamiento.
---

# Limpieza, normalización y tokenización

El preprocesamiento debe ser **una sola función** que se use igual para el corpus, para documentos nuevos (ingesta) y para las consultas. Si la consulta se procesa distinto que el corpus, la recuperación falla.

Los parámetros que dependen del corpus están en la sección `limpieza` de `proyecto.yaml`: `modelo_spacy`, `stemmer`, `caracteres_permitidos`, `simbolos_a_espacio`, `stopwords_extra`, `longitud_minima_token`, `min_tokens_documento`, `palabras_titulo`. El idioma es `datos.idioma`. Léelos de ahí; no los copies en el código.

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
   - `normalizar`: minúsculas; reemplaza cada símbolo de `simbolos_a_espacio` por espacio; elimina dígitos (`\d+`); elimina todo lo que no esté en `caracteres_permitidos` ni sea espacio; quita apóstrofos sueltos y, solo en inglés, la terminación `'s`; colapsa espacios múltiples; `strip()`.
     Para idiomas con acentos, `caracteres_permitidos` debe incluirlos (p. ej. `a-záéíóúñü` en español); si no, se perderían letras.
     Los caracteres que no están en `caracteres_permitidos` se **borran** sin dejar espacio: si `-` no está en `simbolos_a_espacio`, `high-definition` queda como `highdefinition`. Incluye `-` (y `/`) en `simbolos_a_espacio` para separar esas palabras, y documenta la decisión.
   - `tokenizar`: `texto.split()`; descarta tokens de longitud < `longitud_minima_token`; descarta las stopwords de spaCy del idioma (`spacy.lang.<datos.idioma>.stop_words.STOP_WORDS`) **más** `stopwords_extra`. Expón esa lista propia como constante `STOPWORDS_EXTRA` para que sea visible.
   - `lematizar`: spaCy `modelo_spacy` cargado **una vez** a nivel de módulo con `disable=["parser", "ner"]`; usa `token.lemma_`; vuelve a quitar stopwords y tokens cortos después de lematizar.
   - `stemizar`: `nltk.stem.PorterStemmer` si `stemmer` es `porter` (solo inglés); `nltk.stem.SnowballStemmer(<nombre del idioma>)` si es `snowball`.
   - Para el corpus completo usa `nlp.pipe(textos, batch_size=64)` (no un `nlp()` por documento), y comprueba que da el mismo resultado que `preprocesar` documento por documento.

2. Crea `src/limpieza.py` que:
   1. Carga `datos.ruta_raw` y renombra `datos.columna_texto` → `text` y `datos.columna_categoria` → `category`, para que todas las etapas siguientes usen nombres fijos.
   2. Elimina duplicados exactos de `text` con `drop_duplicates(subset="text", keep="first")`. Deben quedar `datos.filas_esperadas − datos.duplicados_esperados` documentos (si esos valores aún son `null`, registra los que quedaron).
   3. Elimina documentos que queden con menos de `min_tokens_documento` tokens tras preprocesar (registra cuántos).
   4. Asigna `doc_id` = `"doc_0000"`, `"doc_0001"`, … en el orden resultante.
   5. Extrae `titulo` = primeras `palabras_titulo` palabras del texto original (si el corpus no separa título y cuerpo, esto es solo para mostrar resultados; si trae una columna de título, úsala y documéntalo).
   6. Genera las columnas:
      - `text_original` (sin cambios)
      - `text_norm` (salida de `normalizar`)
      - `tokens_lemma` (tokens lematizados unidos por espacio)
      - `tokens_stem` (tokens stemizados unidos por espacio)
      - `n_tokens` (len de `tokens_lemma`)
   7. Guarda `data/processed/corpus_clean.csv` con columnas en este orden: `doc_id, category, titulo, text_original, text_norm, tokens_lemma, tokens_stem, n_tokens`. Ninguna celda de tokens debe quedar vacía.
3. Ejecuta `python src/limpieza.py`.
4. Escribe `reports/limpieza.md` con: documentos antes/después, duplicados eliminados, documentos descartados por cortos, tokens promedio antes y después, tamaño de vocabulario con lema y con stem, 3 ejemplos (texto original → tokens_lemma, recortados a 30 palabras), decisiones tomadas y por qué. Números con separador de miles.
5. Guarda `reports/limpieza.json` con `n_antes`, `n_despues`, `duplicados`, `descartados_cortos`, `tokens_promedio`.

## Representación por defecto

Todas las etapas siguientes usan `tokens_lemma`. `tokens_stem` se usa solo para la comparación en EDA y, si sobra tiempo, como variante en evaluación.

## Casi duplicados

`drop_duplicates` solo quita copias idénticas carácter por carácter. Calcula también, con un `TfidfVectorizer` de sklearn sobre `tokens_lemma` (solo para este diagnóstico), cuántos pares de documentos tienen similitud coseno ≥ 0.95 (versiones editadas de un mismo texto) y repórtalo en `reports/limpieza.md`. No los elimines sin que el usuario lo decida: inflan la evaluación cuando una consulta sale de uno de ellos.

## No hagas

- No sobrescribas `data/raw/`.
- No uses otra lista de stopwords sin documentarlo en `reports/limpieza.md`.
- No uses un modelo de spaCy de otro idioma distinto al del corpus.

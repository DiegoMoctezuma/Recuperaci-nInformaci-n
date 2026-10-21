---
name: limpieza
description: Limpia, normaliza, tokeniza y lematiza/stemiza un corpus de textos en el idioma que tenga, eligiendo el modelo, el stemmer y las stopwords a partir de los datos, y expone una función reutilizable de preprocesamiento para documentos nuevos y consultas. Úsala en la etapa limpieza del pipeline o cuando cambie el preprocesamiento.
---

# Limpieza, normalización y tokenización

El preprocesamiento debe ser **una sola función** que se use igual para el corpus, para documentos nuevos (ingesta) y para las consultas. Si la consulta se procesa distinto que el corpus, la recuperación falla.

Lee la sección `limpieza` de `proyecto.yaml` (y `datos.idioma`, que decidió `eda_raw`). Respeta lo fijado; decide lo que esté en `auto` con las reglas de abajo, escríbelo de vuelta y regístralo en `decisiones` con su razón.

## Decide según los datos (si está en `auto`)

| Clave | Regla |
|---|---|
| `modelo_spacy` | Según `datos.idioma`: `en` → `en_core_web_sm`, `es` → `es_core_news_sm`, `fr` → `fr_core_news_sm`, `pt` → `pt_core_news_sm`, `de` → `de_core_news_sm`, `it` → `it_core_news_sm`. Si no está instalado, instálalo con `python -m spacy download <modelo>` y regístralo en `ENTORNO.md`. Si el idioma no tiene modelo, usa `spacy.blank(<idioma>)` sin lematizar (solo stem) y dilo en el reporte. |
| `stemmer` | `porter` si el idioma es inglés; `snowball` con el nombre del idioma en los demás. |
| `caracteres_permitidos` | Letras Unicode (`[^\W\d_]`), es decir, cualquier letra con o sin acento, del alfabeto que sea. Más el apóstrofo solo en inglés. |
| `stopwords_extra` | Términos (ya lematizados) que aparecen en más de 40% de los documentos **y** en todas las categorías con frecuencias parecidas (ninguna categoría con más del doble de su proporción media): no distinguen nada. Máximo 20; lístalos en el reporte. Sin categorías, solo el criterio de 40%. |
| `longitud_minima_token` | `3` en idiomas con alfabeto latino; `2` si el idioma usa palabras cortas con significado (p. ej. chino o japonés tokenizados). |
| `palabras_prohibidas` | Las 3 stopwords más frecuentes del texto original (sirven a la validación para comprobar que se quitaron). |
| `prueba` | Una oración corta escrita por ti en el idioma del corpus, con mayúsculas, un número y una stopword, y la salida que da `preprocesar`; regístrala para que la validación compruebe que el resultado no cambia. |

`simbolos_a_espacio`, `conservar_numeros`, `min_tokens_documento` y `palabras_titulo` los decidió `eda_raw`.

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
   - `normalizar`: minúsculas; cada símbolo de `simbolos_a_espacio` → espacio; si `conservar_numeros` es `false`, elimina dígitos; todo carácter fuera de `caracteres_permitidos` → **espacio** (no se borra, para no fundir palabras); en inglés, quita la terminación `'s` y los apóstrofos sueltos; colapsa espacios; `strip()`.
   - `tokenizar`: `texto.split()`; descarta tokens con menos de `longitud_minima_token` caracteres; descarta las stopwords de spaCy del idioma (`spacy.lang.<idioma>.stop_words.STOP_WORDS`) **más** `stopwords_extra`. Expón la lista propia como constante `STOPWORDS_EXTRA`.
   - `lematizar`: el modelo de spaCy cargado **una vez** a nivel de módulo con `disable=["parser", "ner"]`; usa `token.lemma_` en minúsculas; vuelve a quitar stopwords, tokens cortos y lemas no alfabéticos después de lematizar.
   - `stemizar`: el stemmer decidido, sobre los tokens filtrados.
   - Para el corpus completo usa `nlp.pipe(textos, batch_size=64)` (no un `nlp()` por documento) y comprueba en una muestra de 50 documentos que da lo mismo que `preprocesar` uno por uno.

2. Crea `src/limpieza.py` que:
   1. Carga `datos.ruta_raw` y renombra la columna de texto → `text`, la de categoría → `category` (si no hay, crea `category = "sin_categoria"`), y la de título → `titulo_original` si existe. Así todas las etapas siguientes usan nombres fijos.
   2. Elimina documentos con texto vacío o nulo, y duplicados exactos de `text` con `drop_duplicates(subset="text", keep="first")`.
   3. Elimina documentos que queden con menos de `min_tokens_documento` tokens tras preprocesar (registra cuántos; si son más de 5% del corpus, avisa).
   4. Asigna `doc_id` = `"doc_0000"`, `"doc_0001"`, … (con tantos dígitos como haga falta) en el orden resultante.
   5. `titulo` = `titulo_original` si existe; si no, las primeras `palabras_titulo` palabras del texto original (o el texto completo si `palabras_titulo` es `null`).
   6. Genera `text_original` (sin cambios), `text_norm`, `tokens_lemma` y `tokens_stem` (tokens unidos por espacio) y `n_tokens` (len de `tokens_lemma`).
   7. Guarda `data/processed/corpus_clean.csv` con columnas en este orden: `doc_id, category, titulo, text_original, text_norm, tokens_lemma, tokens_stem, n_tokens`. Ninguna celda de tokens debe quedar vacía.
   8. Si `limpieza.filas_limpias` está en `auto`, escribe `{min: <filas>, max: <filas>}` con las filas que quedaron.
3. Ejecuta `python src/limpieza.py`.
4. **Casi duplicados**: con un `TfidfVectorizer` de sklearn sobre `tokens_lemma` (solo para este diagnóstico), cuenta los pares con similitud coseno ≥ 0.95 y si comparten categoría. No los elimines: repórtalos (inflan la evaluación cuando una consulta sale de uno de ellos).
5. Escribe `reports/limpieza.md` con: documentos antes/después, duplicados eliminados, vacíos y cortos descartados, casi duplicados, tokens promedio antes y después, vocabulario con lema y con stem, 3 ejemplos (texto original → tokens_lemma, recortados a 30 palabras), **decisiones tomadas** (tabla clave → valor → razón). Números con separador de miles.
6. Guarda `reports/limpieza.json` con `n_antes`, `n_despues`, `duplicados`, `descartados_cortos`, `casi_duplicados`, `tokens_promedio`.

## Representación por defecto

Todas las etapas siguientes usan `tokens_lemma`. `tokens_stem` se usa para la comparación en EDA y, si sobra tiempo, como variante en evaluación. Si el idioma no tiene lematizador, `tokens_lemma` contiene los stems y se dice en el reporte.

## No hagas

- No sobrescribas `data/raw/`.
- No uses un modelo de spaCy de un idioma distinto al del corpus.
- No cambies un valor de `proyecto.yaml` que el usuario fijó (sin `auto`).

# Limpieza y normalizacion

## Resumen

| Metrica | Valor |
|---|---|
| Documentos antes | 2,225 |
| Duplicados exactos eliminados | 99 |
| Documentos tras deduplicar | 2,126 |
| Descartados por cortos (< 20 tokens lemma) | 0 |
| Documentos despues | 2,126 |
| Tokens promedio antes (palabras del texto original) | 390.45 |
| Tokens promedio despues (`n_tokens`, lemma) | 181.42 |
| Vocabulario lemma / stem | 24,971 / 21,127 |
| Tiempo de ejecucion | 33.6 s |

## Ejemplos (recortados a 30 palabras)

**doc_0658** (entertainment)

- Original: no uk premiere for rings musical the producers behind the lord of the rings musical have abandoned plans to premiere the show in london because no suitable theatre was available. ...
- tokens_lemma: premiere ring musical producer lord rings musical abandon plan premiere london suitable theatre available debut toronto march find west end theatre sufficient capacity book musical expect london december producer kevin ...

**doc_1734** (business)

- Original: continental may run out of cash shares in continental airlines have tumbled after the firm warned it could run out of cash. in a filing to us regulators the airline ...
- tokens_lemma: continental run cash share continental airlines tumble firm warn run cash filing regulator airline warn inadequate liquidity fail reduce wage cost end february continental cut expect lose million dollar current ...

**doc_1226** (business)

- Original: honda wins china copyright ruling japan s honda has won a copyright case in beijing further evidence that china is taking a tougher line on protecting intellectual property rights. a ...
- tokens_lemma: honda win china copyright rule japan honda win copyright case beijing evidence china tough line protect intellectual property right court rule chongqe lifan industry group stop sell honda brand motorbike ...

## Decisiones y por que

- Una sola funcion (`preprocesar` en `src/preprocesamiento.py`) para corpus, ingesta y consultas; el corpus usa `preprocesar_lote` (`nlp.pipe`, batch_size=64), que produce el mismo resultado.
- Stopwords: `spacy.lang.en.stop_words.STOP_WORDS` mas `STOPWORDS_EXTRA` = ['said', 'mr', 'mrs', 'ms', 'also', 'would', 'could', 'year', 'years', 'new', 'one', 'two']. No se usa ninguna otra lista.
- Normalizacion literal segun la skill: los caracteres fuera de a-z, apostrofo y espacio se **eliminan** (no se sustituyen por espacio), salvo `£` y `$` que se sustituyen por espacio. Consecuencia: palabras con guion se funden (`high-definition` -> `highdefinition`, `e-mail` -> `email`, `wi-fi` -> `wifi`) y los marcadores de marcador deportivo (`6-3`) desaparecen al quitar digitos. Es consistente entre corpus y consultas.
- Apostrofos: el corpus no contiene ninguno; en consultas se quita la terminacion `'s` y luego cualquier apostrofo restante.
- Lematizacion con spaCy `en_core_web_sm` (parser y ner desactivados) sobre los tokens ya filtrados unidos por espacio (sin contexto sintactico completo); tras lematizar se vuelven a filtrar stopwords, tokens < 3 y lemas no alfabeticos.
- Stemming (Porter) aplicado a los tokens filtrados (sin lematizar), no a los lemas.
- Documentos con menos de 20 tokens lemma se descartan antes de asignar `doc_id`.
- `titulo` = primeras 8 palabras del texto original (solo para mostrar resultados).
- `tokens_promedio.antes` cuenta palabras separadas por espacio del texto original de los documentos que se conservan.

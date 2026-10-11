"""Etapa 3: limpieza del corpus BBC. Uso: python src/limpieza.py (desde la raiz del repo)."""
import json
import sys
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocesamiento import (STOPWORDS_EXTRA, normalizar, preprocesar_lote,  # noqa: E402
                              tokenizar, stemizar)

RAW = RAIZ / "data" / "raw" / "bbc-text.csv"
SALIDA = RAIZ / "data" / "processed" / "corpus_clean.csv"
REPORTE_JSON = RAIZ / "reports" / "limpieza.json"
REPORTE_MD = RAIZ / "reports" / "limpieza.md"
MIN_TOKENS = 20


def _recorta(texto: str, n: int = 30) -> str:
    p = str(texto).split()
    return " ".join(p[:n]) + (" ..." if len(p) > n else "")


def main():
    t0 = time.time()
    df = pd.read_csv(RAW)
    n_antes = len(df)

    df = df.drop_duplicates(subset="text", keep="first").reset_index(drop=True)
    duplicados = n_antes - len(df)
    n_dedup = len(df)
    palabras_antes = df["text"].str.split().str.len()

    lemas = preprocesar_lote(df["text"].tolist(), modo="lemma")
    df["_lemma"] = lemas
    corto = df["_lemma"].str.len() < MIN_TOKENS
    descartados = int(corto.sum())
    df = df[~corto].reset_index(drop=True)
    palabras_antes_final = palabras_antes[~corto.values]

    out = pd.DataFrame({
        "doc_id": [f"doc_{i:04d}" for i in range(len(df))],
        "category": df["category"],
        "titulo": df["text"].str.split().str[:8].str.join(" "),
        "text_original": df["text"],
        "text_norm": df["text"].map(normalizar),
        "tokens_lemma": df["_lemma"].map(" ".join),
        "tokens_stem": [" ".join(stemizar(tokenizar(normalizar(t)))) for t in df["text"]],
        "n_tokens": df["_lemma"].str.len(),
    })
    assert out[["doc_id", "category", "tokens_lemma", "tokens_stem"]].notna().all().all()
    assert (out["tokens_lemma"].str.len() > 0).all() and (out["tokens_stem"].str.len() > 0).all()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SALIDA, index=False)

    voc_lemma = len({t for s in out["tokens_lemma"] for t in s.split()})
    voc_stem = len({t for s in out["tokens_stem"] for t in s.split()})
    metricas = {
        "n_antes": int(n_antes),
        "n_despues": int(len(out)),
        "duplicados": int(duplicados),
        "descartados_cortos": descartados,
        "tokens_promedio": {
            "antes": round(float(palabras_antes_final.mean()), 2),
            "despues": round(float(out["n_tokens"].mean()), 2),
        },
        "vocabulario": {"lemma": voc_lemma, "stem": voc_stem},
        "segundos": round(time.time() - t0, 1),
    }
    REPORTE_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORTE_JSON.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")

    ejemplos = out.sample(3, random_state=0)
    ej = "\n".join(
        f"**{r.doc_id}** ({r.category})\n\n- Original: {_recorta(r.text_original)}\n"
        f"- tokens_lemma: {_recorta(r.tokens_lemma)}\n"
        for r in ejemplos.itertuples()
    )
    md = f"""# Limpieza y normalizacion

## Resumen

| Metrica | Valor |
|---|---|
| Documentos antes | {n_antes:,} |
| Duplicados exactos eliminados | {duplicados:,} |
| Documentos tras deduplicar | {n_dedup:,} |
| Descartados por cortos (< {MIN_TOKENS} tokens lemma) | {descartados:,} |
| Documentos despues | {len(out):,} |
| Tokens promedio antes (palabras del texto original) | {metricas['tokens_promedio']['antes']:,.2f} |
| Tokens promedio despues (`n_tokens`, lemma) | {metricas['tokens_promedio']['despues']:,.2f} |
| Vocabulario lemma / stem | {voc_lemma:,} / {voc_stem:,} |
| Tiempo de ejecucion | {metricas['segundos']:,.1f} s |

## Ejemplos (recortados a 30 palabras)

{ej}
## Decisiones y por que

- Una sola funcion (`preprocesar` en `src/preprocesamiento.py`) para corpus, ingesta y consultas; el corpus usa `preprocesar_lote` (`nlp.pipe`, batch_size=64), que produce el mismo resultado.
- Stopwords: `spacy.lang.en.stop_words.STOP_WORDS` mas `STOPWORDS_EXTRA` = {STOPWORDS_EXTRA}. No se usa ninguna otra lista.
- Normalizacion literal segun la skill: los caracteres fuera de a-z, apostrofo y espacio se **eliminan** (no se sustituyen por espacio), salvo `£` y `$` que se sustituyen por espacio. Consecuencia: palabras con guion se funden (`high-definition` -> `highdefinition`, `e-mail` -> `email`, `wi-fi` -> `wifi`) y los marcadores de marcador deportivo (`6-3`) desaparecen al quitar digitos. Es consistente entre corpus y consultas.
- Apostrofos: el corpus no contiene ninguno; en consultas se quita la terminacion `'s` y luego cualquier apostrofo restante.
- Lematizacion con spaCy `en_core_web_sm` (parser y ner desactivados) sobre los tokens ya filtrados unidos por espacio (sin contexto sintactico completo); tras lematizar se vuelven a filtrar stopwords, tokens < 3 y lemas no alfabeticos.
- Stemming (Porter) aplicado a los tokens filtrados (sin lematizar), no a los lemas.
- Documentos con menos de {MIN_TOKENS} tokens lemma se descartan antes de asignar `doc_id`.
- `titulo` = primeras 8 palabras del texto original (solo para mostrar resultados).
- `tokens_promedio.antes` cuenta palabras separadas por espacio del texto original de los documentos que se conservan.
"""
    REPORTE_MD.write_text(md, encoding="utf-8")
    return metricas


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False))

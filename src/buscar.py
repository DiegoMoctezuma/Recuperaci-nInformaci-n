"""Etapa 5: pipeline de consulta (query -> vectorizacion -> similitud/BM25 -> ranking).

Uso como libreria:  sys.path.insert(0, 'src'); from buscar import buscar, recargar
Uso por CLI:        python src/buscar.py "oil prices rise" --metodo bm25 --k 5
                    python src/buscar.py --ejemplos     (Parte D: reports/ejemplos_busqueda.md)
"""
import argparse
import sys
import warnings
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / "models"
REPORTES = RAIZ / "reports"
METODOS = ("count", "tfidf", "bm25", "svd", "w2v", "lda")
COLUMNAS = ["rank", "doc_id", "category", "titulo", "score"]

_models_dir = MODELOS
_cache: dict = {}


def recargar(models_dir=None) -> None:
    """Invalida la cache de modelos (p. ej. tras reconstruir indices). Con `models_dir` apunta
    a otro directorio de modelos (pruebas); sin argumento vuelve a models/ del repo."""
    global _models_dir
    _models_dir = Path(models_dir) if models_dir is not None else MODELOS
    _cache.clear()


def _get(nombre: str):
    """Carga perezosa (una sola vez) de un artefacto de models/."""
    if nombre not in _cache:
        d = _models_dir
        if nombre == "doc_index":
            _cache[nombre] = pd.read_csv(d / "doc_index.csv")
        elif nombre == "w2v":
            from gensim.models import Word2Vec
            _cache[nombre] = (Word2Vec.load(str(d / "w2v.model")).wv, np.load(d / "w2v_docs.npy"))
        else:
            _cache[nombre] = joblib.load(d / f"{nombre}.pkl")
    return _cache[nombre]


def _preprocesar(query: str):
    src = str(Path(__file__).resolve().parent)
    if src not in sys.path:
        sys.path.insert(0, src)
    from preprocesamiento import preprocesar
    return preprocesar(query, modo="lemma")


def _vacio() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS)


def buscar(query: str, metodo: str, k: int = 10) -> pd.DataFrame:
    """Top-k documentos para `query`. metodo in {count, tfidf, bm25, svd, w2v, lda}.
    Devuelve DataFrame con columnas rank, doc_id, category, titulo, score."""
    metodo = str(metodo).lower()
    if metodo not in METODOS:
        raise ValueError(f"metodo debe ser uno de {METODOS}, no {metodo!r}")
    if k < 1:
        raise ValueError("k debe ser >= 1")

    tokens = _preprocesar(query)
    if not tokens:
        warnings.warn("La consulta quedo vacia tras el preprocesamiento; sin resultados.")
        return _vacio()
    texto = " ".join(tokens)

    if metodo in ("count", "tfidf"):
        m = _get(metodo)
        q = m["vectorizer"].transform([texto])
        if q.nnz == 0:
            warnings.warn("Ningun termino de la consulta esta en el vocabulario del indice.")
            return _vacio()
        scores = cosine_similarity(q, m["matrix"]).ravel()
    elif metodo == "svd":
        q_tfidf = _get("tfidf")["vectorizer"].transform([texto])
        if q_tfidf.nnz == 0:
            warnings.warn("Ningun termino de la consulta esta en el vocabulario del indice.")
            return _vacio()
        m = _get("svd")
        scores = cosine_similarity(m["pipeline"].transform(q_tfidf), m["matrix"]).ravel()
    elif metodo == "lda":
        q_count = _get("count")["vectorizer"].transform([texto])
        if q_count.nnz == 0:
            warnings.warn("Ningun termino de la consulta esta en el vocabulario del indice.")
            return _vacio()
        m = _get("lda")
        scores = cosine_similarity(m["lda"].transform(q_count), m["matrix"]).ravel()
    elif metodo == "w2v":
        wv, docs = _get("w2v")
        vecs = [wv[t] for t in tokens if t in wv.key_to_index]
        if not vecs:
            warnings.warn("Ningun termino de la consulta esta en el vocabulario de Word2Vec.")
            return _vacio()
        scores = cosine_similarity(np.mean(vecs, axis=0, keepdims=True), docs).ravel()
    else:  # bm25
        bm25 = _get("bm25")["model"]
        if not any(t in bm25.idf for t in tokens):
            warnings.warn("Ningun termino de la consulta esta en el vocabulario de BM25.")
            return _vacio()
        scores = np.asarray(bm25.get_scores(tokens), dtype=float)

    orden = np.argsort(-scores, kind="stable")[:k]  # desempate estable por orden de fila
    meta = _get("doc_index")
    if len(meta) != len(scores):
        raise RuntimeError("doc_index.csv y los indices tienen distinto numero de documentos; "
                           "reconstruye con python src/indices.py")
    res = meta.iloc[orden][["doc_id", "category", "titulo"]].reset_index(drop=True)
    res.insert(0, "rank", np.arange(1, len(res) + 1))
    res["score"] = scores[orden].astype(float)
    return res[COLUMNAS]


# ---------------------------------------------------------------- Parte D
CONSULTAS_EJEMPLO = [
    ("stock market shares fall", "business"),
    ("election labour party vote", "politics"),
    ("mobile phone software", "tech"),
]


def _celda(s) -> str:
    return str(s).replace("|", "\\|")


def generar_ejemplos(ruta=None, k: int = 5) -> dict:
    """Ejecuta las 3 consultas de la Parte D con los 6 metodos y guarda el top-k en markdown.
    Devuelve {(consulta, metodo): (categoria_dominante, n_dominante)}."""
    ruta = Path(ruta) if ruta is not None else REPORTES / "ejemplos_busqueda.md"
    dominante = {}
    partes = ["# Ejemplos de búsqueda (Parte D)\n",
              f"Top-{k} por consulta y método sobre {len(_get('doc_index')):,} documentos. "
              "Puntaje: similitud coseno (count, tfidf, svd, w2v, lda) o puntaje BM25 (bm25). "
              "Las consultas pasan por el mismo `preprocesar(modo=\"lemma\")` del corpus.\n"]
    for consulta, esperado in CONSULTAS_EJEMPLO:
        partes.append(f"## \"{consulta}\" (esperado: {esperado})\n")
        for m in METODOS:
            r = buscar(consulta, m, k)
            cat, n = Counter(r["category"]).most_common(1)[0]
            dominante[(consulta, m)] = (cat, n)
            partes.append(f"### {m}: categoría dominante del top-{k}: {cat} ({n}/{len(r)})\n")
            partes.append("| rank | doc_id | category | titulo | score |\n|---|---|---|---|---|")
            for x in r.itertuples():
                partes.append(f"| {x.rank} | {x.doc_id} | {x.category} | {_celda(x.titulo)} | {x.score:,.4f} |")
            partes.append("")
    partes.append("## Resumen: categoría dominante del top-5\n")
    partes.append("| consulta (esperado) | " + " | ".join(METODOS) + " |")
    partes.append("|---|" + "---|" * len(METODOS))
    for consulta, esperado in CONSULTAS_EJEMPLO:
        celdas = []
        for m in METODOS:
            cat, n = dominante[(consulta, m)]
            celdas.append(f"{cat} ({n}/{k})")
        partes.append(f"| {consulta} ({esperado}) | " + " | ".join(celdas) + " |")
    partes.append("")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(partes), encoding="utf-8")
    return dominante


def main(argv=None):
    ap = argparse.ArgumentParser(description="Busqueda sobre el corpus BBC")
    ap.add_argument("query", nargs="?", help="texto de la consulta")
    ap.add_argument("--metodo", default="tfidf", choices=METODOS)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--ejemplos", action="store_true",
                    help="genera reports/ejemplos_busqueda.md (Parte D)")
    a = ap.parse_args(argv)
    if a.ejemplos:
        for (c, m), (cat, n) in generar_ejemplos().items():
            print(f"{c!r:32s} {m:6s} -> {cat} ({n}/5)")
        return
    if not a.query:
        ap.error("falta la consulta (o usa --ejemplos)")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = buscar(a.query, a.metodo, a.k)
    for x in w:
        print(f"AVISO: {x.message}", file=sys.stderr)
    if len(r):
        print(r.to_string(index=False, formatters={"score": "{:.4f}".format}))


if __name__ == "__main__":
    main()

"""Etapa 5: construccion de indices de recuperacion (Count, TF-IDF, BM25, SVD/LSA, Word2Vec, LDA).

Uso: python src/indices.py (desde la raiz del repo).
Importable sin efectos secundarios: todo el trabajo ocurre en `construir_indices()`.
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "data" / "processed" / "corpus_clean.csv"
MODELOS = RAIZ / "models"
REPORTES = RAIZ / "reports"

SEED = 42

# Etiquetas cortas de los topicos LDA (escritas a partir de sus 10 palabras principales,
# para el corpus de 2,126 documentos con random_state=42). Se guardan junto con las
# palabras de referencia para poder reasignarlas por solapamiento si, tras una ingesta,
# el orden de los topicos cambia. Un topico sin correspondencia (< MIN_SOLAPE palabras)
# queda como "sin etiqueta (revisar)".
LDA_ETIQUETAS_REF = {
    0: ('Economía y precios', ['rise', 'market', 'sale', 'growth', 'price', 'economy', 'rate', 'fall', 'month', 'economic']),
    1: ('Música', ['music', 'band', 'song', 'album', 'number', 'chart', 'record', 'single', 'artist', 'rock']),
    2: ('Leyes y tribunales', ['law', 'government', 'case', 'court', 'tell', 'lord', 'rule', 'right', 'police', 'company']),
    3: ('Política británica y elecciones', ['labour', 'party', 'election', 'people', 'blair', 'government', 'minister', 'tory', 'brown', 'plan']),
    4: ('Rugby y fútbol: partidos', ['win', 'minute', 'ireland', 'second', 'ball', 'try', 'run', 'game', 'penalty', 'italy']),
    5: ('Yukos, deuda y Rusia (mixto)', ['open', 'bank', 'yukos', 'world', 'set', 'win', 'country', 'russian', 'play', 'debt']),
    6: ('Tecnología móvil y usuarios', ['people', 'game', 'technology', 'mobile', 'phone', 'service', 'use', 'user', 'computer', 'network']),
    7: ('Fútbol: jugadores y clubes', ['game', 'play', 'win', 'england', 'player', 'club', 'time', 'good', 'team', 'think']),
    8: ('Cine y premios', ['film', 'good', 'award', 'star', 'win', 'include', 'actor', 'director', 'oscar', 'prize']),
    9: ('Empresas, ofertas y fusiones', ['company', 'china', 'firm', 'share', 'deal', 'offer', 'india', 'bid', 'market', 'airline']),
}
MIN_SOLAPE = 4


def _densidad_pct(m) -> float:
    """% de entradas distintas de cero (2 decimales)."""
    total = m.shape[0] * m.shape[1]
    nnz = m.nnz if hasattr(m, "nnz") else int(np.count_nonzero(m))
    return round(100.0 * nnz / total, 2)


def _info(matriz, vocab, t0):
    return {
        "dimensiones": [int(matriz.shape[0]), int(matriz.shape[1])],
        "vocabulario": int(vocab),
        "densidad_pct": _densidad_pct(matriz),
        "tiempo_s": round(time.perf_counter() - t0, 2),
    }


def _etiquetar_topicos(palabras_por_topico):
    """Etiqueta cada topico por solapamiento de palabras con LDA_ETIQUETAS_REF (asignacion
    uno a uno, voraz por mayor solapamiento; exige >= MIN_SOLAPE palabras en comun)."""
    pares = sorted(((len(set(p) & set(ref)), i, j)
                    for i, p in enumerate(palabras_por_topico)
                    for j, (_, ref) in LDA_ETIQUETAS_REF.items()),
                   key=lambda x: (-x[0], x[1], x[2]))
    etiquetas = ["sin etiqueta (revisar)"] * len(palabras_por_topico)
    usados_i, usados_j = set(), set()
    for n, i, j in pares:
        if n < MIN_SOLAPE:
            break
        if i in usados_i or j in usados_j:
            continue
        etiquetas[i] = LDA_ETIQUETAS_REF[j][0]
        usados_i.add(i)
        usados_j.add(j)
    return etiquetas


def _figura_svd(var_acum, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    from estilo_graficas import DPI

    comp = np.arange(1, len(var_acum) + 1)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(comp, var_acum * 100, color="#1f77b4", lw=2)
    ax.axhline(var_acum[-1] * 100, color="#7f7f7f", ls="--", lw=1)
    ax.annotate(f"{len(comp)} componentes: {var_acum[-1] * 100:,.2f}%",
                xy=(comp[-1], var_acum[-1] * 100), xytext=(-8, -18),
                textcoords="offset points", ha="right", fontsize=9)
    ax.set_title("SVD (LSA) sobre TF-IDF: varianza explicada acumulada")
    ax.set_xlabel("Número de componentes")
    ax.set_ylabel("Varianza explicada acumulada (%)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)


def construir_indices(corpus_path=CORPUS, models_dir=MODELOS, reports_dir=REPORTES) -> dict:
    """Construye TODOS los indices desde cero y devuelve el dict escrito en reports/indices.json."""
    from gensim.models import Word2Vec
    from rank_bm25 import BM25Okapi
    from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import Normalizer

    corpus_path, models_dir, reports_dir = Path(corpus_path), Path(models_dir), Path(reports_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "figuras").mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(corpus_path)
    textos = df["tokens_lemma"].astype(str).tolist()
    assert df["tokens_lemma"].notna().all() and all(t.strip() for t in textos), "tokens_lemma vacio"
    n_docs = len(df)
    resumen = {}

    # --- mapeo fila -> documento
    df[["doc_id", "category", "titulo"]].to_csv(models_dir / "doc_index.csv", index=False)

    # --- CountVectorizer
    t0 = time.perf_counter()
    count = CountVectorizer(analyzer=str.split, min_df=2, max_df=0.95)
    X_count = count.fit_transform(textos)
    resumen["count"] = _info(X_count, len(count.vocabulary_), t0)
    joblib.dump({"vectorizer": count, "matrix": X_count}, models_dir / "count.pkl")

    # --- TF-IDF
    t0 = time.perf_counter()
    tfidf = TfidfVectorizer(analyzer=str.split, min_df=2, max_df=0.95, sublinear_tf=True, norm="l2")
    X_tfidf = tfidf.fit_transform(textos)
    resumen["tfidf"] = _info(X_tfidf, len(tfidf.vocabulary_), t0)
    joblib.dump({"vectorizer": tfidf, "matrix": X_tfidf}, models_dir / "tfidf.pkl")

    # --- BM25
    t0 = time.perf_counter()
    corpus_tokens = [t.split() for t in textos]
    bm25 = BM25Okapi(corpus_tokens, k1=1.5, b=0.75)
    nnz_bm25 = sum(len(f) for f in bm25.doc_freqs)
    resumen["bm25"] = {
        "dimensiones": [n_docs, len(bm25.idf)],
        "vocabulario": len(bm25.idf),
        "densidad_pct": round(100.0 * nnz_bm25 / (n_docs * len(bm25.idf)), 2),
        "tiempo_s": round(time.perf_counter() - t0, 2),
    }
    joblib.dump({"model": bm25}, models_dir / "bm25.pkl")

    # --- SVD (LSA) sobre TF-IDF
    t0 = time.perf_counter()
    svd = TruncatedSVD(n_components=200, random_state=SEED)
    pipe_svd = make_pipeline(svd, Normalizer(copy=False))
    X_svd = pipe_svd.fit_transform(X_tfidf)
    resumen["svd"] = _info(X_svd, len(tfidf.vocabulary_), t0)
    joblib.dump({"pipeline": pipe_svd, "matrix": X_svd}, models_dir / "svd.pkl")
    var_acum = np.cumsum(svd.explained_variance_ratio_)
    resumen["svd"]["varianza_explicada_acumulada_pct"] = round(float(var_acum[-1]) * 100, 2)
    resumen["svd"]["varianza_acumulada_por_componentes_pct"] = {
        str(c): round(float(var_acum[c - 1]) * 100, 2) for c in (10, 50, 100, 150, 200)
    }
    _figura_svd(var_acum, reports_dir / "figuras" / "svd_varianza.png")

    # --- Word2Vec (extra). seed=42 + workers=1 => reproducible (verificado con distintos PYTHONHASHSEED).
    t0 = time.perf_counter()
    w2v = Word2Vec(sentences=corpus_tokens, vector_size=100, window=5, min_count=2, sg=1,
                   epochs=20, seed=SEED, workers=1)
    X_w2v = np.zeros((n_docs, w2v.vector_size), dtype=np.float32)
    for i, toks in enumerate(corpus_tokens):
        vecs = [w2v.wv[t] for t in toks if t in w2v.wv.key_to_index]
        if vecs:
            v = np.mean(vecs, axis=0)
            X_w2v[i] = v / (np.linalg.norm(v) or 1.0)
    resumen["w2v"] = _info(X_w2v, len(w2v.wv.key_to_index), t0)
    w2v.save(str(models_dir / "w2v.model"))
    np.save(models_dir / "w2v_docs.npy", X_w2v)

    # --- LDA (extra) sobre la matriz de CountVectorizer
    t0 = time.perf_counter()
    lda = LatentDirichletAllocation(n_components=10, learning_method="batch", max_iter=20,
                                    random_state=SEED)
    lda.fit(X_count)
    X_lda = lda.transform(X_count)
    resumen["lda"] = _info(X_lda, len(count.vocabulary_), t0)
    joblib.dump({"lda": lda, "matrix": X_lda}, models_dir / "lda.pkl")

    vocab = np.array(count.get_feature_names_out())
    palabras = [vocab[np.argsort(-comp, kind="stable")[:10]].tolist() for comp in lda.components_]
    etiquetas = _etiquetar_topicos(palabras)
    pd.DataFrame({"topico": range(10), "etiqueta": etiquetas,
                  "palabras": [", ".join(p) for p in palabras]}
                 ).to_csv(reports_dir / "lda_topicos.csv", index=False)
    resumen["lda"]["topicos"] = [{"topico": i, "etiqueta": e, "palabras": p}
                                 for i, (e, p) in enumerate(zip(etiquetas, palabras))]

    salida = {"n_docs": n_docs, "metodos": resumen}
    (reports_dir / "indices.json").write_text(
        json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    return salida


if __name__ == "__main__":
    res = construir_indices()
    for nombre, m in res["metodos"].items():
        f, c = m["dimensiones"]
        print(f"{nombre:6s} {f:,} x {c:,}  vocab={m['vocabulario']:,}  "
              f"densidad={m['densidad_pct']:,.2f}%  tiempo={m['tiempo_s']:,.2f}s")
    print("SVD varianza acumulada:", f"{res['metodos']['svd']['varianza_explicada_acumulada_pct']:,.2f}%")

"""Etapa 6: evaluacion de la recuperacion (P@5, P@10, MAP@10, nDCG@10, MRR, latencia).

Relevancia: un documento es relevante si su categoria coincide con la categoria esperada de la
consulta (proxy; el corpus no trae juicios de relevancia). El doc_origen de las consultas
automaticas se excluye del ranking.

Uso (desde la raiz):  python src/evaluacion.py
Como modulo:          import evaluacion; metricas = evaluacion.evaluar()
"""
import json
import math
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import consultas as _consultas  # noqa: E402
from buscar import METODOS, buscar  # noqa: E402
from estilo_graficas import DPI, ORDEN_CATEGORIAS, PALETA_CATEGORIAS  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CONSULTAS_CSV = RAIZ / "data" / "processed" / "consultas.csv"
REPORTES = RAIZ / "reports"
FIGURAS = REPORTES / "figuras"
K = 10
COL_METRICAS = ["p_at_5", "p_at_10", "ap_at_10", "ndcg_at_10", "rr"]
# Colores por metodo: hex de la paleta del proyecto (+ gris para el sexto).
COLOR_METODO = dict(zip(METODOS, list(PALETA_CATEGORIAS.values()) + ["#7f7f7f"]))


# ------------------------------------------------------------------ metricas
def precision_at_k(rel, k):
    """Relevantes en el top-k / k (posiciones faltantes cuentan como no relevantes)."""
    return sum(rel[:k]) / k


def average_precision(rel, n_relevantes, k=K):
    """Suma de P@i en cada posicion relevante i<=k, dividida entre min(k, n_relevantes)."""
    hits, suma = 0, 0.0
    for i, r in enumerate(rel[:k], start=1):
        if r:
            hits += 1
            suma += hits / i
    return suma / min(k, n_relevantes)


def ndcg_at_k(rel, k=K):
    """Ganancia binaria, descuento 1/log2(pos+1); IDCG con k relevantes."""
    dcg = sum(r / math.log2(i + 1) for i, r in enumerate(rel[:k], start=1))
    idcg = sum(1 / math.log2(i + 1) for i in range(1, k + 1))
    return dcg / idcg


def reciprocal_rank(rel, k=K):
    """1 / posicion del primer relevante dentro del top-k (0 si no hay)."""
    for i, r in enumerate(rel[:k], start=1):
        if r:
            return 1 / i
    return 0.0


def _pruebas_metricas():
    """Casos a mano. Caso A: rel=[1,0,1,0,0,0,0,0,0,0], con 10+ relevantes en el corpus."""
    a = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    assert precision_at_k(a, 5) == 0.40
    assert precision_at_k(a, 10) == 0.20
    # AP = (1/1 + 2/3) / 10
    assert abs(average_precision(a, 503) - (1 + 2 / 3) / 10) < 1e-12
    # DCG = 1/log2(2) + 1/log2(4) = 1.5 ; IDCG = sum_{i=1..10} 1/log2(i+1) = 4.5436...
    idcg = sum(1 / math.log2(i + 1) for i in range(1, 11))
    assert abs(idcg - 4.543559) < 1e-5
    assert abs(ndcg_at_k(a) - 1.5 / idcg) < 1e-12 and abs(ndcg_at_k(a) - 0.33015) < 1e-4
    assert reciprocal_rank(a) == 1.0
    todo, nada = [1] * 10, [0] * 10
    for f in (lambda r: precision_at_k(r, 5), lambda r: precision_at_k(r, 10),
              lambda r: average_precision(r, 503), ndcg_at_k, reciprocal_rank):
        assert abs(f(todo) - 1.0) < 1e-12 and f(nada) == 0.0
    # primer relevante en la posicion 4 -> RR = 0.25 ; lista corta rellenada con ceros
    assert reciprocal_rank([0, 0, 0, 1, 0, 0, 0, 0, 0, 0]) == 0.25
    assert abs(average_precision([1, 1, 1] + [0] * 7, 503) - 0.3) < 1e-12


_pruebas_metricas()


# ------------------------------------------------------------------ evaluacion
def _top10(query, metodo, doc_origen):
    """Top-10 sin doc_origen (pide k=11), con la latencia de la llamada en ms."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t0 = time.perf_counter()
        res = buscar(query, metodo, k=K + 1)
        ms = (time.perf_counter() - t0) * 1000
    if isinstance(doc_origen, str) and doc_origen:
        res = res[res["doc_id"] != doc_origen]
    return res.head(K).reset_index(drop=True), ms


def _graficas(por_consulta, metricas, por_categoria):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    tot = metricas[metricas["tipo"] == "total"].set_index("metodo")

    orden = tot["map_at_10"].sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    barras = ax.bar(orden.index, orden.values, color=[COLOR_METODO[m] for m in orden.index])
    for b, v in zip(barras, orden.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.4f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, min(1.0, orden.max() + 0.12))
    ax.set_xlabel("Método de recuperación")
    ax.set_ylabel("MAP@10")
    ax.set_title("MAP@10 por método (115 consultas, relevancia = misma categoría)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "eval_map_por_metodo.png", dpi=DPI)
    plt.close(fig)

    pivote = por_categoria.pivot(index="metodo", columns="categoria", values="map_at_10")
    pivote = pivote.loc[list(orden.index), ORDEN_CATEGORIAS]
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    im = ax.imshow(pivote.values, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pivote.columns)), pivote.columns)
    ax.set_yticks(range(len(pivote.index)), pivote.index)
    for i in range(pivote.shape[0]):
        for j in range(pivote.shape[1]):
            v = pivote.values[i, j]
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    color="white" if v > 0.6 else "black", fontsize=9)
    fig.colorbar(im, ax=ax, label="MAP@10")
    ax.set_xlabel("Categoría esperada de la consulta")
    ax.set_ylabel("Método de recuperación")
    ax.set_title("MAP@10 por método y categoría")
    fig.tight_layout()
    fig.savefig(FIGURAS / "eval_heatmap_categoria.png", dpi=DPI)
    plt.close(fig)

    lat = tot["latencia_ms"].sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    barras = ax.bar(lat.index, lat.values, color=[COLOR_METODO[m] for m in lat.index])
    for b, v in zip(barras, lat.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, lat.max() * 1.15)
    ax.set_xlabel("Método de recuperación")
    ax.set_ylabel("Latencia media por consulta (ms)")
    ax.set_title("Latencia por método (preprocesamiento + búsqueda, sin carga de modelos)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURAS / "eval_latencia.png", dpi=DPI)
    plt.close(fig)


def evaluar(consultas=None, guardar=True) -> pd.DataFrame:
    """Evalua los 6 metodos. Devuelve el DataFrame de reports/metricas.csv y (si guardar=True)
    escribe metricas_por_consulta.csv, metricas.csv, metricas_por_categoria.csv, figuras y json."""
    if consultas is None:
        consultas = _consultas.generar_consultas() if not CONSULTAS_CSV.exists() else \
            pd.read_csv(CONSULTAS_CSV, keep_default_na=False)
    consultas = consultas.fillna({"doc_origen": ""})
    corpus_cat = pd.read_csv(RAIZ / "data" / "processed" / "corpus_clean.csv",
                             usecols=["doc_id", "category"])
    n_cat = corpus_cat["category"].value_counts().to_dict()
    assert all(v > K for v in n_cat.values())

    filas, incompletas, top3 = [], {m: 0 for m in METODOS}, {}
    for metodo in METODOS:
        _top10("stock market shares fall", metodo, "")  # calentamiento: carga del modelo
        for q in consultas.itertuples():
            res, ms = _top10(q.query, metodo, q.doc_origen)
            rel = [int(c == q.categoria_esperada) for c in res["category"]]
            if len(rel) < K:
                incompletas[metodo] += 1
            rel = rel + [0] * (K - len(rel))
            # relevantes en el corpus sin contar doc_origen (la consulta auto es de su categoria)
            n_rel = n_cat[q.categoria_esperada] - (1 if q.doc_origen else 0)
            filas.append({
                "metodo": metodo, "query_id": q.query_id, "tipo": q.tipo,
                "categoria": q.categoria_esperada,
                "p_at_5": precision_at_k(rel, 5), "p_at_10": precision_at_k(rel, K),
                "ap_at_10": average_precision(rel, n_rel), "ndcg_at_10": ndcg_at_k(rel),
                "rr": reciprocal_rank(rel), "latencia_ms": ms, "n_resultados": int((res["rank"] > 0).sum()),
            })
            top3[(metodo, q.query_id)] = [
                f"{r.doc_id} ({r.category}) {r.titulo}" for r in res.head(3).itertuples()]
    pc = pd.DataFrame(filas)

    cols = ["p_at_5", "p_at_10", "ap_at_10", "ndcg_at_10", "rr", "latencia_ms"]
    partes = []
    for tipo in ("auto", "manual", "total"):
        sub = pc if tipo == "total" else pc[pc["tipo"] == tipo]
        g = sub.groupby("metodo")[cols].mean().reindex(list(METODOS)).reset_index()
        g.insert(1, "tipo", tipo)
        partes.append(g)
    m = pd.concat(partes, ignore_index=True).rename(columns={"ap_at_10": "map_at_10", "rr": "mrr"})
    metricas = m[["metodo", "tipo", "p_at_5", "p_at_10", "map_at_10", "ndcg_at_10", "mrr",
                  "latencia_ms"]].round(4)

    cat = (pc.groupby(["metodo", "categoria"])
             .agg(map_at_10=("ap_at_10", "mean"), n_consultas=("ap_at_10", "size")).reset_index())
    cat["map_at_10"] = cat["map_at_10"].round(4)
    cat["metodo"] = pd.Categorical(cat["metodo"], categories=list(METODOS), ordered=True)
    cat["categoria"] = pd.Categorical(cat["categoria"], categories=ORDEN_CATEGORIAS, ordered=True)
    cat = cat.sort_values(["metodo", "categoria"]).reset_index(drop=True)
    cat["metodo"] = cat["metodo"].astype(str)
    cat["categoria"] = cat["categoria"].astype(str)

    num = metricas.drop(columns=["metodo", "tipo", "latencia_ms"])
    assert ((num >= 0) & (num <= 1)).all().all()

    if guardar:
        REPORTES.mkdir(parents=True, exist_ok=True)
        pc_out = pc.rename(columns={"ap_at_10": "ap_at_10", "rr": "rr"}).copy()
        pc_out["metodo"] = pd.Categorical(pc_out["metodo"], categories=list(METODOS), ordered=True)
        pc_out = pc_out.sort_values(["metodo", "query_id"]).reset_index(drop=True)
        pc_out["metodo"] = pc_out["metodo"].astype(str)
        for c in ["p_at_5", "p_at_10", "ap_at_10", "ndcg_at_10", "rr"]:
            pc_out[c] = pc_out[c].round(4)
        pc_out["latencia_ms"] = pc_out["latencia_ms"].round(3)
        pc_out.to_csv(REPORTES / "metricas_por_consulta.csv", index=False, encoding="utf-8")
        metricas.to_csv(REPORTES / "metricas.csv", index=False, encoding="utf-8", float_format="%.4f")
        cat.to_csv(REPORTES / "metricas_por_categoria.csv", index=False, encoding="utf-8",
                   float_format="%.4f")
        _graficas(pc, metricas, cat)
        _guardar_json(pc, consultas, metricas, cat, incompletas, top3)
    return metricas


def _guardar_json(pc, consultas, metricas, cat, incompletas, top3):
    """Numeros clave y candidatos a casos de discrepancia (dispersion de AP@10 entre metodos)."""
    ap = pc.pivot(index="query_id", columns="metodo", values="ap_at_10")[list(METODOS)]
    info = consultas.set_index("query_id")
    candidatos = {}
    for tipo in ("auto", "manual"):
        ids = [i for i in ap.index if info.loc[i, "tipo"] == tipo]
        # dispersion entre los 5 metodos distintos de lda (lda se reporta aparte) y total
        spread = (ap.loc[ids].max(axis=1) - ap.loc[ids].min(axis=1)).sort_values(ascending=False)
        candidatos[tipo] = [{
            "query_id": i, "query": info.loc[i, "query"], "categoria": info.loc[i, "categoria_esperada"],
            "doc_origen": info.loc[i, "doc_origen"],
            "ap_at_10": {m: round(float(ap.loc[i, m]), 4) for m in METODOS},
            "top3": {m: top3[(m, i)] for m in METODOS},
        } for i in spread.index[:6]]
    # diferencias pareadas de AP@10 entre metodos con IC95% bootstrap (remuestreo de consultas)
    rng = np.random.default_rng(42)
    pares = {}
    for a, b in [("w2v", "svd"), ("svd", "bm25"), ("bm25", "tfidf"), ("tfidf", "count"),
                 ("bm25", "count"), ("lda", "bm25")]:
        d = (ap[a] - ap[b]).to_numpy()
        medias = [rng.choice(d, len(d)).mean() for _ in range(5000)]
        lo, hi = np.percentile(medias, [2.5, 97.5])
        pares[f"{a}-{b}"] = {"dif_media_map": round(float(d.mean()), 4), "ic95": [round(float(lo), 4), round(float(hi), 4)],
                             "consultas_a_gana": int((d > 0).sum()), "consultas_b_gana": int((d < 0).sum())}
    out = {
        "n_consultas": int(len(consultas)),
        "resultados_incompletos_por_metodo": incompletas,
        "metricas": metricas.to_dict(orient="records"),
        "map_por_categoria": cat.to_dict(orient="records"),
        "comparaciones_pareadas_map": pares,
        "casos_candidatos": candidatos,
    }
    (REPORTES / "evaluacion.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                              encoding="utf-8")


def main():
    metricas = evaluar()
    with pd.option_context("display.width", 200):
        print(metricas.to_string(index=False))


if __name__ == "__main__":
    main()

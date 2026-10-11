"""Graficas con la identidad del deck (regeneradas desde reports/*.csv, reports/*.json y el corpus limpio).

Una idea por grafica: el elemento del que habla el titulo va en `acento`, el resto en `neutro`.
Uso:  python src/presentacion/graficas.py     (escribe presentacion/figuras/*.png)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.ticker import FuncFormatter

from presentacion import diseno as D

REPORTES = D.RAIZ / "reports"
P = D.PALETA
DPI = 200
NOMBRE_METODO = {"w2v": "Word2Vec", "svd": "SVD", "lda": "LDA", "bm25": "BM25", "tfidf": "TF-IDF", "count": "Conteo"}


def _configurar_fuente() -> str:
    try:
        fm.findfont("Calibri", fallback_to_default=False)
        familia = "Calibri"
    except ValueError:
        familia = "DejaVu Sans"
    plt.rcParams.update({
        "font.family": familia, "font.size": 15, "text.color": P["tinta"], "axes.edgecolor": P["neutro"],
        "axes.labelcolor": P["tinta_suave"], "xtick.color": P["tinta_suave"], "ytick.color": P["tinta_suave"],
        "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none",
    })
    return familia


def _guardar(fig, nombre: str) -> Path:
    D.DIR_FIG.mkdir(parents=True, exist_ok=True)
    ruta = D.DIR_FIG / nombre
    fig.savefig(ruta, dpi=DPI, transparent=True)
    plt.close(fig)
    return ruta


def _miles(x, _pos=None) -> str:
    return f"{x:,.0f}"


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


# ------------------------------------------------------------------ datos
def _frecuencias() -> tuple[pd.DataFrame, Counter]:
    df = pd.read_csv(D.RAIZ / "data" / "processed" / "corpus_clean.csv", usecols=["category", "tokens_lemma"])
    df["tokens_lemma"] = df["tokens_lemma"].fillna("")
    c = Counter()
    for t in df["tokens_lemma"]:
        c.update(t.split())
    return df, c


# ------------------------------------------------------------------ graficas
def cat_distribucion() -> Path:
    raw = json.loads((REPORTES / "eda_raw.json").read_text(encoding="utf-8"))
    cuentas = raw["conteo_categorias"]
    pct = raw["porcentaje_categorias"]
    orden = sorted(cuentas, key=cuentas.get)           # de menor a mayor: la mayor queda arriba
    top2 = set(sorted(cuentas, key=cuentas.get)[-2:])
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    y = np.arange(len(orden))
    ax.barh(y, [cuentas[c] for c in orden], color=[P["acento"] if c in top2 else P["neutro"] for c in orden], height=0.62)
    for i, c in enumerate(orden):
        ax.text(cuentas[c] + 8, i, f"{cuentas[c]:,}  ·  {pct[c]:.2f}%", va="center", fontsize=15,
                color=P["tinta"], fontweight="bold" if c in top2 else "normal")
    ax.set_yticks(y, [D.NOMBRE_CATEGORIA[c] for c in orden], fontsize=16, color=P["tinta"])
    ax.set_xlim(0, max(cuentas.values()) * 1.42)
    ax.set_xticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    return _guardar(fig, "cat_distribucion.png")


def zipf(frec: Counter) -> Path:
    est = json.loads((REPORTES / "eda_corpus.json").read_text(encoding="utf-8"))
    f = np.array(sorted(frec.values(), reverse=True), dtype=float)
    r = np.arange(1, len(f) + 1)
    s, C, rmax = est["zipf_s"], est["zipf_C"], est["zipf_rango_ajuste"][1]
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    ax.scatter(r, f, s=7, color=P["neutro"], linewidths=0, zorder=2)
    rr = np.array([1, rmax], dtype=float)
    ax.plot(rr, C * rr ** (-s), color=P["acento"], lw=3.2, zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.annotate(f"s = {s:.4f}", xy=(60, C * 60 ** (-s)), xytext=(160, C * 60 ** (-s) * 2.2), fontsize=19,
                color=P["acento_texto"], fontweight="bold", va="bottom")
    ax.annotate("people", xy=(1, f[0]), xytext=(1.25, f[0] * 1.05), fontsize=14, color=P["tinta_suave"], va="center")
    ax.set_xlabel("Rango de la palabra (de más a menos frecuente)", fontsize=14)
    ax.set_ylabel("Frecuencia", fontsize=14)
    ax.xaxis.set_major_formatter(FuncFormatter(_miles))
    ax.yaxis.set_major_formatter(FuncFormatter(_miles))
    ax.yaxis.grid(True, color=P["neutro"], alpha=0.4, lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return _guardar(fig, "zipf.png")


def heaps(df: pd.DataFrame) -> Path:
    est = json.loads((REPORTES / "eda_corpus.json").read_text(encoding="utf-8"))
    toks = df["tokens_lemma"].map(str.split)
    orden = np.random.RandomState(est["heaps_semilla"]).permutation(len(toks))   # misma semilla que la etapa EDA
    plano = [t for i in orden for t in toks.iloc[i]]
    cod, _ = pd.factorize(pd.Series(plano))
    nuevo = np.zeros(len(cod), dtype=np.int64)
    _, primera = np.unique(cod, return_index=True)
    nuevo[primera] = 1
    v = np.cumsum(nuevo)
    n = np.arange(est["heaps_paso_tokens"], len(plano) + 1, est["heaps_paso_tokens"])
    v_pts = v[n - 1]
    assert len(plano) == est["N"] and int(v[-1]) == est["V"], "el corpus no coincide con reports/eda_corpus.json"
    K, beta = est["heaps_K"], est["heaps_beta"]
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    ax.scatter(n, v_pts, s=26, color=P["neutro"], linewidths=0, zorder=2)
    xs = np.linspace(est["heaps_paso_tokens"], len(plano), 200)
    ax.plot(xs, K * xs ** beta, color=P["acento"], lw=3.2, zorder=3)
    ax.text(len(plano) * 0.52, K * (len(plano) * 0.52) ** beta * 0.78, f"β = {beta:.4f}", fontsize=19,
            color=P["acento_texto"], fontweight="bold", ha="center", va="top")
    ax.set_xlabel("Tokens leídos", fontsize=14)
    ax.set_ylabel("Palabras distintas", fontsize=14)
    ax.xaxis.set_major_formatter(FuncFormatter(_miles))
    ax.yaxis.set_major_formatter(FuncFormatter(_miles))
    ax.set_xlim(0, len(plano) * 1.03)
    ax.set_ylim(0, v[-1] * 1.08)
    ax.set_xticks(np.arange(0, len(plano), 100000))
    ax.set_yticks(np.arange(0, 25001, 5000))
    ax.yaxis.grid(True, color=P["neutro"], alpha=0.4, lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return _guardar(fig, "heaps.png")


def _tinte(color: str, t: float) -> tuple:
    """Mezcla del color con blanco: t=0 color puro, t=1 blanco."""
    c = np.array(to_rgb(color))
    return tuple(c + (1 - c) * t)


def wordcloud_categoria(df: pd.DataFrame, cat: str) -> Path:
    from wordcloud import WordCloud
    por_cat = {c: Counter(" ".join(g).split()) for c, g in df.groupby("category")["tokens_lemma"]}
    total = Counter()
    for c in por_cat.values():
        total.update(c)
    # tamano ~ frecuencia en la categoria x proporcion de esa palabra que cae en la categoria (resalta lo propio)
    pesos = {w: f * (f / total[w]) for w, f in por_cat[cat].items()}
    color = D.CATEGORIAS[cat]
    cmap = LinearSegmentedColormap.from_list("cat", [_tinte(color, 0.45), to_rgb(color)])
    pesos_max = max(pesos.values())

    def color_func(word, **kw):
        t = (pesos.get(word, 0) / pesos_max) ** 0.5
        r, g, b = (int(255 * x) for x in cmap(t)[:3])
        return f"rgb({r},{g},{b})"

    wc = WordCloud(width=1170, height=690, mode="RGBA", background_color=None, max_words=55, prefer_horizontal=0.95,
                   font_path=D.ruta_fuente("Calibri", True), color_func=color_func, random_state=42,
                   margin=4, relative_scaling=0.5).generate_from_frequencies(pesos)
    ruta = D.DIR_FIG / f"wordcloud_{cat}.png"
    D.DIR_FIG.mkdir(parents=True, exist_ok=True)
    wc.to_image().save(ruta, dpi=(300, 300))
    return ruta


def _metricas_total() -> pd.DataFrame:
    m = pd.read_csv(REPORTES / "metricas.csv")
    return m[m["tipo"] == "total"].set_index("metodo")


def map_metodos() -> Path:
    m = _metricas_total()["map_at_10"].sort_values()
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    y = np.arange(len(m))
    ax.barh(y, m.values, color=[P["acento"] if k == "bm25" else P["neutro"] for k in m.index], height=0.62)
    for i, (k, v) in enumerate(m.items()):
        ax.text(v + 0.012, i, _pct(v), va="center", fontsize=16, color=P["tinta"],
                fontweight="bold" if k == "bm25" else "normal")
    ax.set_yticks(y, [NOMBRE_METODO[k] for k in m.index], fontsize=16, color=P["tinta"])
    ax.set_xlim(0, 1.12)
    ax.set_xticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("MAP@10 (115 consultas)", fontsize=14, loc="left")
    fig.tight_layout()
    return _guardar(fig, "map_metodos.png")


def mancuernas() -> Path:
    m = pd.read_csv(REPORTES / "metricas.csv").pivot(index="metodo", columns="tipo", values="map_at_10")
    m = m.sort_values("auto")                      # el mejor (auto) queda arriba
    fig, ax = plt.subplots(figsize=(12.1, 3.5))
    y = np.arange(len(m))
    for i, k in enumerate(m.index):
        a, mn = m.loc[k, "auto"], m.loc[k, "manual"]
        ax.plot([a, mn], [i, i], color=P["neutro"], lw=3, zorder=1, solid_capstyle="round")
        ax.scatter([mn], [i], s=130, color=P["neutro"], zorder=2, edgecolors=P["tinta_suave"], linewidths=1.2)
        ax.scatter([a], [i], s=150, color=P["acento"], zorder=3)
        ax.text(a - 0.012, i, _pct(a), ha="right", va="center", fontsize=15, color=P["tinta"],
                fontweight="bold" if k in ("w2v", "count") else "normal")
        ax.text(mn + 0.012, i, _pct(mn), ha="left", va="center", fontsize=15, color=P["tinta_suave"])
    top = len(m) - 1
    ax.text(m.loc[m.index[top], "auto"], top + 0.62, "titulares de 8 palabras", ha="center", va="bottom", fontsize=15,
            color=P["acento_texto"], fontweight="bold")
    ax.text(m.loc[m.index[top], "manual"], top + 0.62, "consultas manuales", ha="center", va="bottom", fontsize=15,
            color=P["tinta_suave"], fontweight="bold")
    ax.set_yticks(y, [NOMBRE_METODO[k] for k in m.index], fontsize=16, color=P["tinta"])
    ax.set_xlim(0.56, 1.08)
    ax.set_ylim(-0.6, len(m) - 0.1 + 0.7)
    ax.set_xticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    return _guardar(fig, "mancuernas_tipo_consulta.png")


def heatmap_categoria() -> Path:
    h = pd.read_csv(REPORTES / "metricas_por_categoria.csv").pivot(index="metodo", columns="categoria", values="map_at_10")
    orden = list(_metricas_total().sort_values("map_at_10", ascending=False).index)
    h = h.loc[orden, ["business", "entertainment", "politics", "sport", "tech"]]
    cmap = LinearSegmentedColormap.from_list("neu", [P["fondo"], P["neutro"], P["tinta_suave"]])
    fig, ax = plt.subplots(figsize=(12.1, 3.6))
    ax.imshow(h.values, cmap=cmap, vmin=0.5, vmax=1.0, aspect="auto")
    mn = np.unravel_index(np.argmin(h.values), h.shape)
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):
            v = h.values[i, j]
            ax.text(j, i, _pct(v), ha="center", va="center", fontsize=15,
                    color="white" if v > 0.86 else P["tinta"], fontweight="bold" if (i, j) == mn else "normal")
    ax.add_patch(plt.Rectangle((mn[1] - 0.5, mn[0] - 0.5), 1, 1, fill=False, ec=P["acento"], lw=3.5))
    ax.set_xticks(range(5), [D.NOMBRE_CATEGORIA[c] for c in h.columns], fontsize=15, color=P["tinta"])
    ax.set_yticks(range(len(h)), [NOMBRE_METODO[k] for k in h.index], fontsize=15, color=P["tinta"])
    ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.tight_layout()
    return _guardar(fig, "heatmap_metodo_categoria.png")


def latencia() -> Path:
    m = _metricas_total()["latencia_ms"].sort_values()
    fig, ax = plt.subplots(figsize=(8.0, 4.0))
    y = np.arange(len(m))
    ax.barh(y, m.values, color=[P["acento"] if k == "w2v" else P["neutro"] for k in m.index], height=0.62)
    for i, (k, v) in enumerate(m.items()):
        ax.text(v + 0.2, i, f"{v:.2f} ms", va="center", fontsize=16, color=P["tinta"],
                fontweight="bold" if k == "w2v" else "normal")
    ax.set_yticks(y, [NOMBRE_METODO[k] for k in m.index], fontsize=16, color=P["tinta"])
    ax.set_xlim(0, m.max() * 1.3)
    ax.set_xticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    return _guardar(fig, "latencia.png")


def generar_todas() -> list[Path]:
    familia = _configurar_fuente()
    print("fuente de graficas:", familia)
    df, frec = _frecuencias()
    rutas = [cat_distribucion(), zipf(frec), heaps(df)]
    rutas += [wordcloud_categoria(df, c) for c in ("sport", "politics", "tech")]
    rutas += [map_metodos(), mancuernas(), heatmap_categoria(), latencia()]
    return rutas


if __name__ == "__main__":
    for r in generar_todas():
        print("escrito", r.relative_to(D.RAIZ))

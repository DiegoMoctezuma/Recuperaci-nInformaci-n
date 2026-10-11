"""Analisis exploratorio del corpus BBC News.

Uso (desde la raiz del repo):
    python src/eda.py --modo raw
    python src/eda.py --modo corpus

Como modulo:
    import eda; metricas = eda.eda_raw(); metricas = eda.eda_corpus()
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estilo_graficas import DPI, ORDEN_CATEGORIAS, PALETA_CATEGORIAS  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RAW_CSV = RAIZ / "data" / "raw" / "bbc-text.csv"
REPORTES = RAIZ / "reports"
FIGURAS = REPORTES / "figuras"

SIMBOLOS = ["£", "$", "%", "-"]


def _n(x):
    return f"{int(x):,}"


def _p(x):
    return f"{x:.2f}%"


def _f(x):
    return f"{x:,.2f}"


def _describe(serie):
    return {
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "min": int(serie.min()),
        "max": int(serie.max()),
        "p25": float(serie.quantile(0.25)),
        "p75": float(serie.quantile(0.75)),
    }


def _tabla_long(df, col, cats):
    filas = {"global": _describe(df[col])}
    for c in cats:
        filas[c] = _describe(df.loc[df["category"] == c, col])
    return filas


def _md_tabla_long(stats):
    out = ["| Grupo | Media | Mediana | Mín | Máx | P25 | P75 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for g, s in stats.items():
        out.append(
            f"| {g} | {_f(s['media'])} | {_f(s['mediana'])} | {_n(s['min'])} | {_n(s['max'])} "
            f"| {_f(s['p25'])} | {_f(s['p75'])} |"
        )
    return "\n".join(out)


def _graf_categorias(conteo, ruta):
    fig, ax = plt.subplots(figsize=(8, 5))
    cats = list(conteo.index)
    barras = ax.bar(cats, conteo.values, color=[PALETA_CATEGORIAS[c] for c in cats])
    total = conteo.sum()
    for b, v in zip(barras, conteo.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}\n({v / total * 100:.2f}%)",
                ha="center", va="bottom", fontsize=9)
    ax.set_title("Documentos por categoría (corpus BBC News, crudo)")
    ax.set_xlabel("Categoría")
    ax.set_ylabel("Número de documentos")
    ax.set_ylim(0, conteo.max() * 1.18)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, format="png")
    plt.close(fig)


def _graf_longitudes(df, cats, ruta):
    fig, ax = plt.subplots(figsize=(8, 5))
    datos = [df.loc[df["category"] == c, "n_palabras"].values for c in cats]
    bp = ax.boxplot(datos, tick_labels=cats, patch_artist=True, medianprops={"color": "black"})
    for patch, c in zip(bp["boxes"], cats):
        patch.set_facecolor(PALETA_CATEGORIAS[c])
        patch.set_alpha(0.8)
    ax.set_title("Longitud de los documentos por categoría (en palabras)")
    ax.set_xlabel("Categoría")
    ax.set_ylabel("Longitud (palabras)")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, format="png")
    plt.close(fig)


def eda_raw(ruta_csv=RAW_CSV, dir_reportes=REPORTES):
    """EDA del corpus crudo. Escribe figuras, eda_raw.md y eda_raw.json; devuelve el dict de metricas."""
    ruta_csv = Path(ruta_csv)
    dir_reportes = Path(dir_reportes)
    dir_fig = dir_reportes / "figuras"
    dir_fig.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ruta_csv)
    n_docs = len(df)
    cats = [c for c in ORDEN_CATEGORIAS if c in set(df["category"].dropna())]
    cats += sorted(set(df["category"].dropna()) - set(cats))

    # Categorias
    conteo = df["category"].value_counts().reindex(cats)
    pct = conteo / n_docs * 100

    # Nulos
    nulos = {c: int(df[c].isna().sum()) for c in df.columns}
    vacios = int((df["text"].fillna("").str.strip() == "").sum())

    # Duplicados exactos en text
    dup_extra = df.duplicated(subset="text", keep="first")
    dup_todas = df.duplicated(subset="text", keep=False)
    n_dup = int(dup_extra.sum())
    dup_por_cat = df.loc[dup_extra, "category"].value_counts().reindex(cats).fillna(0).astype(int)
    grupos = df[dup_todas].groupby("text")["category"].agg(["size", "nunique"])
    n_grupos_dup = int(len(grupos))
    n_grupos_cat_conflicto = int((grupos["nunique"] > 1).sum())
    n_filas_en_grupos = int(dup_todas.sum())
    n_tras_dedup = n_docs - n_dup
    conteo_dedup = df.loc[~dup_extra, "category"].value_counts().reindex(cats)

    # Longitudes
    texto = df["text"].fillna("")
    df["n_palabras"] = texto.str.split().str.len()
    df["n_caracteres"] = texto.str.len()
    long_pal = _tabla_long(df, "n_palabras", cats)
    long_car = _tabla_long(df, "n_caracteres", cats)

    # Caracteres no alfabeticos
    con_digitos = texto.str.contains(r"\d", regex=True)
    pct_dig = float(con_digitos.mean() * 100)
    pct_simb = {s: float(texto.str.contains(s, regex=False).mean() * 100) for s in SIMBOLOS}
    con_algun_simbolo = texto.apply(lambda t: any(s in t for s in SIMBOLOS))
    pct_algun_simbolo = float(con_algun_simbolo.mean() * 100)
    pct_dig_cat = {c: float(con_digitos[df["category"] == c].mean() * 100) for c in cats}
    # Inventario de otros caracteres no alfanumericos ni espacio (para decisiones de limpieza)
    todos = pd.Series(list("".join(texto.tolist()))).value_counts()
    otros = todos[[ch for ch in todos.index if not (ch.isalnum() or ch.isspace())]]
    otros_top = {ch: int(v) for ch, v in otros.head(15).items()}
    no_ascii = {ch: int(v) for ch, v in todos.items() if ord(ch) > 127}
    pct_mayus = float(texto.str.contains(r"[A-Z]", regex=True).mean() * 100)

    # Figuras
    _graf_categorias(conteo, dir_fig / "raw_categorias.png")
    _graf_longitudes(df, cats, dir_fig / "raw_longitudes.png")

    metricas = {
        "n_docs": int(n_docs),
        "n_duplicados": n_dup,
        "n_docs_tras_deduplicar": int(n_tras_dedup),
        "duplicados_por_categoria": {c: int(v) for c, v in dup_por_cat.items()},
        "n_grupos_duplicados": n_grupos_dup,
        "n_filas_en_grupos_duplicados": n_filas_en_grupos,
        "grupos_duplicados_con_categorias_distintas": n_grupos_cat_conflicto,
        "conteo_categorias": {c: int(v) for c, v in conteo.items()},
        "porcentaje_categorias": {c: round(float(v), 2) for c, v in pct.items()},
        "conteo_categorias_tras_deduplicar": {c: int(v) for c, v in conteo_dedup.items()},
        "nulos": nulos,
        "textos_vacios": vacios,
        "longitud_media": long_pal["global"]["media"],
        "longitud_palabras": long_pal,
        "longitud_caracteres": long_car,
        "pct_docs_con_digitos": pct_dig,
        "pct_docs_con_digitos_por_categoria": pct_dig_cat,
        "pct_docs_con_simbolo": pct_simb,
        "pct_docs_con_algun_simbolo": pct_algun_simbolo,
        "pct_docs_con_mayusculas": pct_mayus,
        "otros_caracteres_top": otros_top,
        "caracteres_no_ascii": no_ascii,
    }

    # Reporte md
    g = long_pal["global"]
    md = []
    md.append("# EDA del corpus crudo (modo raw)\n")
    md.append("## Resumen\n")
    md.append(f"- Entrada: `data/raw/bbc-text.csv` con {_n(n_docs)} documentos y columnas {', '.join(f'`{c}`' for c in df.columns[:2])}.")
    md.append(f"- Categorías: {len(cats)} ({', '.join(cats)}).")
    md.append(f"- Nulos: {_n(sum(nulos.values()))}; textos vacíos: {_n(vacios)}.")
    md.append(f"- Duplicados exactos en `text`: {_n(n_dup)} filas sobrantes ({_p(n_dup / n_docs * 100)}); quedarían {_n(n_tras_dedup)} documentos.")
    md.append(f"- Longitud media: {_f(g['media'])} palabras (mediana {_f(g['mediana'])}).")
    md.append(f"- Documentos con dígitos: {_p(pct_dig)}; con algún símbolo (`£ $ % -`): {_p(pct_algun_simbolo)}.\n")
    md.append("## Categorías\n")
    md.append("| Categoría | Documentos | Porcentaje |\n|---|---:|---:|")
    for c in cats:
        md.append(f"| {c} | {_n(conteo[c])} | {_p(pct[c])} |")
    md.append(f"| **total** | {_n(n_docs)} | {_p(100)} |\n")
    md.append("![Documentos por categoría](figuras/raw_categorias.png)\n")
    md.append("## Calidad (nulos y duplicados)\n")
    md.append("Nulos por columna:\n")
    md.append("| Columna | Nulos |\n|---|---:|")
    for c, v in nulos.items():
        md.append(f"| {c} | {_n(v)} |")
    md.append("")
    md.append(f"Duplicados exactos en `text` (se cuentan las copias sobrantes, conservando la primera aparición): **{_n(n_dup)}**, "
              f"repartidos en {_n(n_grupos_dup)} grupos de texto repetido ({_n(n_filas_en_grupos)} filas involucradas). "
              f"Grupos con categorías contradictorias: {_n(n_grupos_cat_conflicto)}.\n")
    md.append("| Categoría | Duplicados sobrantes | % de la categoría | Documentos tras deduplicar |\n|---|---:|---:|---:|")
    for c in cats:
        md.append(f"| {c} | {_n(dup_por_cat[c])} | {_p(dup_por_cat[c] / conteo[c] * 100)} | {_n(conteo_dedup[c])} |")
    md.append(f"| **total** | {_n(n_dup)} | {_p(n_dup / n_docs * 100)} | {_n(n_tras_dedup)} |\n")
    md.append("## Longitudes\n")
    md.append("### En palabras (`text.str.split().str.len()`)\n")
    md.append(_md_tabla_long(long_pal) + "\n")
    md.append("![Longitud por categoría](figuras/raw_longitudes.png)\n")
    md.append("### En caracteres\n")
    md.append(_md_tabla_long(long_car) + "\n")
    md.append("### Caracteres no alfabéticos\n")
    md.append(f"- Documentos con al menos un dígito: {_p(pct_dig)} ("
              + ", ".join(f"{c} {_p(v)}" for c, v in pct_dig_cat.items()) + ").")
    for s in SIMBOLOS:
        md.append(f"- Documentos con `{s}`: {_p(pct_simb[s])}.")
    md.append(f"- Documentos con al menos uno de `£ $ % -`: {_p(pct_algun_simbolo)}.")
    md.append(f"- Documentos con mayúsculas: {_p(pct_mayus)}.")
    md.append("- Otros caracteres no alfanuméricos más frecuentes (carácter: apariciones): "
              + ", ".join(f"`{ch}` {_n(v)}" for ch, v in otros_top.items()) + ".")
    md.append("- Caracteres no ASCII: " + (", ".join(f"`{ch}` {_n(v)}" for ch, v in no_ascii.items()) or "ninguno") + ".\n")
    md.append("## Hallazgos que afectan la limpieza\n")
    md.append(f"- Quitar los {_n(n_dup)} duplicados exactos en `text` (conservar la primera aparición); el corpus pasa a {_n(n_tras_dedup)} documentos.")
    if n_grupos_cat_conflicto == 0:
        md.append("- Ningún grupo duplicado tiene categorías contradictorias, así que deduplicar no introduce ambigüedad de etiqueta.")
    else:
        md.append(f"- {_n(n_grupos_cat_conflicto)} grupos duplicados tienen categorías distintas: decidir cuál conservar.")
    md.append(f"- Nulos/vacíos: {_n(sum(nulos.values()) + vacios)}; " + ("no hace falta imputar ni descartar." if sum(nulos.values()) + vacios == 0 else "descartar esas filas."))
    md.append(f"- {_p(pct_dig)} de los documentos contienen dígitos: decidir si se conservan los números (cifras, años) o se eliminan; si se eliminan, se pierde información como años o importes.")
    md.append(f"- Símbolos `£ $ % -` presentes en {_p(pct_algun_simbolo)} de los documentos: si se eliminan puntuación y símbolos, `-` une palabras compuestas (p. ej. `high-definition`) y `£ $ %` acompañan cifras.")
    md.append("- El texto ya viene en minúsculas, sin comas ni comillas (aparentemente sustituidas por dobles espacios) y conserva el punto final de oración; conviene normalizar espacios múltiples y separar puntuación pegada a palabras antes de tokenizar.")
    md.append(f"- Las longitudes son muy heterogéneas (mín {_n(g['min'])}, máx {_n(g['max'])} palabras): considerar el efecto en la normalización por longitud al indexar (p. ej. TF-IDF, BM25).")
    md.append("- Las categorías están desbalanceadas moderadamente; tenerlo en cuenta al evaluar la recuperación por categoría.\n")
    (dir_reportes / "eda_raw.md").write_text("\n".join(md), encoding="utf-8")
    (dir_reportes / "eda_raw.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    return metricas


CORPUS_CSV = RAIZ / "data" / "processed" / "corpus_clean.csv"

ZIPF_RANGO_MAX = 1000
HEAPS_PASO = 5000
SEMILLA = 42
TOP_GLOBAL = 30
TOP_CATEGORIA = 15
TOP_EXCLUSIVAS = 10


def _ajuste_loglog(x, y):
    """Ajuste lineal log10(y) = a + b*log10(x) con numpy.polyfit; devuelve (pendiente, intercepto, R2)."""
    lx, ly = np.log10(np.asarray(x, dtype=float)), np.log10(np.asarray(y, dtype=float))
    b, a = np.polyfit(lx, ly, 1)
    pred = a + b * lx
    ss_res = float(np.sum((ly - pred) ** 2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2))
    return float(b), float(a), 1 - ss_res / ss_tot


def _fmt_miles(ax, eje="y"):
    f = matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}" if v >= 1 else f"{v:g}")
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def _graf_zipf(frec, s, a, r2, ruta):
    rangos = np.arange(1, len(frec) + 1)
    n_aj = min(ZIPF_RANGO_MAX, len(frec))
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.loglog(rangos, frec, ".", color="#1f77b4", markersize=3, label="Frecuencia observada")
    ra = np.arange(1, n_aj + 1)
    ax.loglog(ra, 10 ** a * ra ** (-s), "-", color="#d62728", linewidth=2,
              label=f"Ajuste rangos 1–{n_aj:,}: s = {s:.3f}, R² = {r2:.3f}")
    ax.axvline(n_aj, color="gray", linestyle=":", linewidth=1)
    ax.set_title("Ley de Zipf: rango vs. frecuencia (tokens_lemma, escala log-log)")
    ax.set_xlabel("Rango (log)")
    ax.set_ylabel("Frecuencia (log)")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    _fmt_miles(ax, "x")
    _fmt_miles(ax, "y")
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, format="png")
    plt.close(fig)


def _graf_heaps(n, v, K, beta, r2, ruta):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(n, v, "o", color="#1f77b4", markersize=3.5, label="Observada (orden aleatorio, semilla 42)")
    ax.plot(n, K * n ** beta, "-", color="#d62728", linewidth=2,
            label=f"Ajuste V = K·n^β: K = {K:.2f}, β = {beta:.3f}, R² = {r2:.3f}")
    ax.set_title("Ley de Heaps: crecimiento del vocabulario (tokens_lemma)")
    ax.set_xlabel("Tokens acumulados (n)")
    ax.set_ylabel("Tamaño del vocabulario (V)")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    _fmt_miles(ax, "x")
    _fmt_miles(ax, "y")
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI, format="png")
    plt.close(fig)


def _wordcloud(frecuencias, ruta):
    from wordcloud import WordCloud

    wc = WordCloud(width=1600, height=900, background_color="white", random_state=SEMILLA, max_words=150)
    wc.generate_from_frequencies({k: int(v) for k, v in frecuencias.items()})
    wc.to_image().save(ruta, format="PNG", dpi=(DPI, DPI))


def eda_corpus(ruta_csv=CORPUS_CSV, dir_reportes=REPORTES):
    """EDA del corpus limpio. Escribe CSV, figuras, eda_corpus.md y eda_corpus.json; devuelve el dict de metricas."""
    ruta_csv = Path(ruta_csv)
    dir_reportes = Path(dir_reportes)
    dir_fig = dir_reportes / "figuras"
    dir_fig.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ruta_csv, keep_default_na=False)
    n_docs = len(df)
    presentes = set(df["category"])
    cats = [c for c in ORDEN_CATEGORIAS if c in presentes] + sorted(presentes - set(ORDEN_CATEGORIAS))
    toks = df["tokens_lemma"].astype(str).str.split()

    # 1. Vocabulario
    frec = pd.Series(Counter(t for ts in toks for t in ts)).sort_values(kind="stable", ascending=False)
    frec = frec.iloc[np.lexsort((frec.index.values, -frec.values))]  # desempate alfabetico: determinista
    N = int(frec.sum())
    V = int(len(frec))
    hapax = int((frec == 1).sum())
    pct_hapax = hapax / V * 100

    frec_cat = {}
    for c in cats:
        cnt = Counter(t for ts in toks[df["category"] == c] for t in ts)
        s_c = pd.Series(cnt)
        frec_cat[c] = s_c.iloc[np.lexsort((s_c.index.values, -s_c.values))]
    cat_por_termino = {}
    for c in cats:
        for t in frec_cat[c].index:
            cat_por_termino.setdefault(t, []).append(c)
    exclusivas = {}
    for c in cats:
        ex = frec_cat[c][[len(cat_por_termino[t]) == 1 for t in frec_cat[c].index]]
        exclusivas[c] = {"n": int(len(ex)), "top": [(t, int(v)) for t, v in ex.head(TOP_EXCLUSIVAS).items()]}

    filas = []
    for r, (t, v) in enumerate(frec.head(TOP_GLOBAL).items(), 1):
        filas.append({"ambito": "global", "rango": r, "termino": t, "frecuencia": int(v),
                      "porcentaje_tokens": round(v / N * 100, 4)})
    for c in cats:
        n_c = int(frec_cat[c].sum())
        for r, (t, v) in enumerate(frec_cat[c].head(TOP_CATEGORIA).items(), 1):
            filas.append({"ambito": c, "rango": r, "termino": t, "frecuencia": int(v),
                          "porcentaje_tokens": round(v / n_c * 100, 4)})
    pd.DataFrame(filas).to_csv(dir_reportes / "vocabulario_top.csv", index=False, encoding="utf-8")

    # 2. Zipf
    f = frec.values.astype(float)
    n_aj = min(ZIPF_RANGO_MAX, len(f))
    pend, interc, zipf_r2 = _ajuste_loglog(np.arange(1, n_aj + 1), f[:n_aj])
    zipf_s = -pend
    _graf_zipf(f, zipf_s, interc, zipf_r2, dir_fig / "zipf.png")

    # 3. Heaps: documentos en orden aleatorio (semilla 42), registro cada 5,000 tokens
    orden = np.random.RandomState(SEMILLA).permutation(n_docs)
    plano = [t for i in orden for t in toks.iloc[i]]
    codigos, _ = pd.factorize(pd.Series(plano))
    es_nuevo = np.zeros(len(codigos), dtype=np.int64)
    _, primera = np.unique(codigos, return_index=True)
    es_nuevo[primera] = 1
    v_acum = np.cumsum(es_nuevo)
    n_pts = np.arange(HEAPS_PASO, len(plano) + 1, HEAPS_PASO)
    v_pts = v_acum[n_pts - 1]
    beta, a_h, heaps_r2 = _ajuste_loglog(n_pts, v_pts)
    heaps_K = float(10 ** a_h)
    _graf_heaps(n_pts, v_pts, heaps_K, beta, heaps_r2, dir_fig / "heaps.png")

    # 4. Wordclouds
    _wordcloud(frec, dir_fig / "wordcloud_global.png")
    for c in cats:
        _wordcloud(frec_cat[c], dir_fig / f"wordcloud_{c}.png")

    # 5. Lema vs. stem
    v_stem = len({t for ts in df["tokens_stem"].astype(str).str.split() for t in ts})
    n_stem = int(df["tokens_stem"].astype(str).str.split().str.len().sum())
    reduccion = (1 - v_stem / V) * 100

    long_doc = toks.str.len()
    metricas = {
        "n_docs": int(n_docs),
        "N": N,
        "V": V,
        "hapax": hapax,
        "hapax_pct_vocabulario": round(pct_hapax, 2),
        "zipf_s": zipf_s,
        "zipf_r2": zipf_r2,
        "zipf_C": float(10 ** interc),
        "zipf_rango_ajuste": [1, int(n_aj)],
        "heaps_K": heaps_K,
        "heaps_beta": beta,
        "heaps_r2": heaps_r2,
        "heaps_puntos": int(len(n_pts)),
        "heaps_semilla": SEMILLA,
        "heaps_paso_tokens": HEAPS_PASO,
        "V_lemma": V,
        "V_stem": int(v_stem),
        "N_stem": n_stem,
        "reduccion_vocabulario_stem_vs_lemma_pct": round(reduccion, 2),
        "longitud_media_tokens": float(long_doc.mean()),
        "vocabulario_por_categoria": {c: int(len(frec_cat[c])) for c in cats},
        "tokens_por_categoria": {c: int(frec_cat[c].sum()) for c in cats},
        "top_global": [(t, int(v)) for t, v in frec.head(TOP_GLOBAL).items()],
        "exclusivas_por_categoria": exclusivas,
        "zipf_dentro_de_0.6_1.5": bool(0.6 <= zipf_s <= 1.5),
        "heaps_dentro_de_0.3_0.8": bool(0.3 <= beta <= 0.8),
        "heaps_dentro_de_0.4_0.7": bool(0.4 <= beta <= 0.7),
    }

    # 6. Reporte md
    md = []
    md.append("# EDA del corpus limpio (modo corpus)\n")
    md.append(f"Entrada: `data/processed/corpus_clean.csv` ({_n(n_docs)} documentos), columna `tokens_lemma`.\n")
    md.append("## Vocabulario\n")
    md.append(f"- Tamaño del corpus (N): **{_n(N)}** tokens (media {_f(long_doc.mean())} por documento).")
    md.append(f"- Tamaño del vocabulario (V): **{_n(V)}** tipos.")
    md.append(f"- Hapax legomena: **{_n(hapax)}** ({_p(pct_hapax)} del vocabulario; {_p(hapax / N * 100)} de los tokens).\n")
    md.append("Top 30 global (completo y top 15 por categoría en `vocabulario_top.csv`):\n")
    md.append("| Rango | Término | Frecuencia | % de tokens |\n|---:|---|---:|---:|")
    for r, (t, v) in enumerate(frec.head(TOP_GLOBAL).items(), 1):
        md.append(f"| {r} | {t} | {_n(v)} | {_p(v / N * 100)} |")
    md.append("")
    md.append("### Vocabulario por categoría\n")
    md.append("| Categoría | Tokens | Vocabulario | Términos exclusivos | Top 10 exclusivos (frecuencia) |\n|---|---:|---:|---:|---|")
    for c in cats:
        top_ex = ", ".join(f"{t} ({_n(v)})" for t, v in exclusivas[c]["top"])
        md.append(f"| {c} | {_n(frec_cat[c].sum())} | {_n(len(frec_cat[c]))} | {_n(exclusivas[c]['n'])} | {top_ex} |")
    md.append("")
    md.append("### Top 15 por categoría\n")
    md.append("| Categoría | Términos |\n|---|---|")
    for c in cats:
        md.append(f"| {c} | " + ", ".join(f"{t} ({_n(v)})" for t, v in frec_cat[c].head(TOP_CATEGORIA).items()) + " |")
    md.append("")
    md.append("## Zipf\n")
    md.append(f"Ajuste `log f = log C − s·log r` con `numpy.polyfit` (log10) sobre los rangos 1 a {_n(n_aj)}:\n")
    md.append(f"- **s = {zipf_s:.4f}**, C = {_f(10 ** interc)}, **R² = {zipf_r2:.4f}**.")
    md.append(f"- Rango esperado para validación: 0.6 a 1.5 → {'dentro' if metricas['zipf_dentro_de_0.6_1.5'] else 'FUERA'} del rango.\n")
    md.append("![Ley de Zipf](figuras/zipf.png)\n")
    md.append("## Heaps\n")
    md.append(f"Documentos en orden aleatorio (semilla {SEMILLA}), registro cada {_n(HEAPS_PASO)} tokens ({_n(len(n_pts))} puntos); ajuste `V = K·n^β` en log-log:\n")
    md.append(f"- **K = {_f(heaps_K)}**, **β = {beta:.4f}**, **R² = {heaps_r2:.4f}**.")
    md.append(f"- Rango esperado para validación: 0.3 a 0.8 → {'dentro' if metricas['heaps_dentro_de_0.3_0.8'] else 'FUERA'}; "
              f"rango típico en inglés 0.4 a 0.7 → {'dentro' if metricas['heaps_dentro_de_0.4_0.7'] else 'FUERA'}.\n")
    md.append("![Ley de Heaps](figuras/heaps.png)\n")
    md.append("## Wordclouds\n")
    md.append("Generadas con frecuencias de `tokens_lemma` (`generate_from_frequencies`, `random_state=42`, `max_words=150`).\n")
    md.append("- [Global](figuras/wordcloud_global.png)")
    for c in cats:
        md.append(f"- [{c}](figuras/wordcloud_{c}.png)")
    md.append("")
    md.append("![Wordcloud global](figuras/wordcloud_global.png)\n")
    for c in cats:
        md.append(f"![Wordcloud {c}](figuras/wordcloud_{c}.png)\n")
    md.append("## Lema vs. stem\n")
    md.append("| Representación | Tokens | Vocabulario |\n|---|---:|---:|")
    md.append(f"| `tokens_lemma` | {_n(N)} | {_n(V)} |")
    md.append(f"| `tokens_stem` | {_n(n_stem)} | {_n(v_stem)} |\n")
    md.append(f"El stemming reduce el vocabulario en {_n(V - v_stem)} tipos ({_p(reduccion)}) respecto a la lematización "
              f"({'más' if v_stem < V else 'no más'} agresivo al colapsar variantes), a costa de formas menos legibles y de fusionar palabras de significado distinto.\n")
    md.append("## Conclusiones para la indexación\n")
    md.append(f"- El índice tendrá {_n(V)} términos (lemas) sobre {_n(N)} tokens; {_p(pct_hapax)} del vocabulario son hapax, que casi no discriminan entre documentos pero inflan el índice: considerar `min_df=2` si se busca compactar.")
    md.append(f"- Zipf con s = {zipf_s:.3f} (R² = {zipf_r2:.3f}): pocos términos concentran gran parte de los tokens; las palabras más frecuentes aportan poco peso discriminativo y justifican ponderación por IDF (TF-IDF/BM25) o una lista de stopwords adicional.")
    md.append(f"- Heaps con β = {beta:.3f} (K = {_f(heaps_K)}): el vocabulario sigue creciendo con el corpus, así que consultas con términos no vistos serán frecuentes; el crecimiento es "
              f"{'sublineal, como se espera en texto' if beta < 1 else 'casi lineal'}.")
    md.append(f"- Lema vs. stem: el stem comprime el vocabulario {_p(reduccion)} ({_n(v_stem)} vs. {_n(V)}), lo que favorece la cobertura (recall) al unir variantes; el lema conserva más precisión y legibilidad. Conviene evaluar ambas en la etapa de recuperación.")
    md.append("- Los términos exclusivos y los top por categoría muestran vocabulario temático claro (ver tablas), lo que sugiere que la recuperación basada en términos separará bien las categorías.\n")
    (dir_reportes / "eda_corpus.md").write_text("\n".join(md), encoding="utf-8")
    (dir_reportes / "eda_corpus.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    return metricas


def main(argv=None):
    ap = argparse.ArgumentParser(description="EDA del corpus BBC News")
    ap.add_argument("--modo", choices=["raw", "corpus"], required=True)
    args = ap.parse_args(argv)
    if args.modo == "raw":
        m = eda_raw()
        print(f"eda_raw OK: n_docs={m['n_docs']:,} n_duplicados={m['n_duplicados']:,} longitud_media={m['longitud_media']:.2f}")
        return 0
    m = eda_corpus()
    print(f"eda_corpus OK: N={m['N']:,} V={m['V']:,} hapax={m['hapax']:,} zipf_s={m['zipf_s']:.3f} "
          f"zipf_r2={m['zipf_r2']:.3f} heaps_beta={m['heaps_beta']:.3f} heaps_r2={m['heaps_r2']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

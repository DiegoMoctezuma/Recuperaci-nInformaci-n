"""Analisis exploratorio del corpus BBC News.

Uso (desde la raiz del repo):
    python src/eda.py --modo raw
    python src/eda.py --modo corpus   # aun no implementado

Como modulo:
    import eda; metricas = eda.eda_raw()
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
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


def eda_corpus():
    raise NotImplementedError("El modo corpus aún no está implementado: su entrada data/processed/corpus_clean.csv todavía no existe.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="EDA del corpus BBC News")
    ap.add_argument("--modo", choices=["raw", "corpus"], required=True)
    args = ap.parse_args(argv)
    if args.modo == "raw":
        m = eda_raw()
        print(f"eda_raw OK: n_docs={m['n_docs']:,} n_duplicados={m['n_duplicados']:,} longitud_media={m['longitud_media']:.2f}")
        return 0
    print("Modo corpus: no implementado todavía (falta data/processed/corpus_clean.csv).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

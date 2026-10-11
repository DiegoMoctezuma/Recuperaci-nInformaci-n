"""Etapa 5: ingesta de noticias nuevas (preprocesa, deduplica, asigna doc_id, reconstruye indices).

Uso: python src/ingesta.py --archivo nuevas.csv      (columnas `text` y opcional `category`)
Como libreria: from ingesta import ingestar; ids = ingestar(["texto ..."], ["tech"])
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from indices import CORPUS, MODELOS, REPORTES, construir_indices  # noqa: E402
from limpieza import MIN_TOKENS  # noqa: E402  (mismo umbral de documentos cortos que la limpieza)
from preprocesamiento import normalizar, preprocesar_lote, stemizar, tokenizar  # noqa: E402

CATEGORIA_DESCONOCIDA = "desconocida"
COLUMNAS_CORPUS = ["doc_id", "category", "titulo", "text_original", "text_norm",
                   "tokens_lemma", "tokens_stem", "n_tokens"]

# Resumen de la ultima llamada a ingestar() (para informes y pruebas).
ultimo_resumen: dict = {}


def ingestar(textos: list[str], categorias: list[str] | None = None,
             corpus_path=CORPUS, models_dir=MODELOS, reports_dir=REPORTES) -> list[str]:
    """Agrega noticias nuevas al corpus, reconstruye todos los indices y devuelve los doc_ids nuevos.

    Descarta: textos no validos/vacios, duplicados exactos (contra el corpus y dentro del lote)
    y documentos con menos de MIN_TOKENS tokens lemma (misma regla que `limpieza`).
    Las rutas por defecto son las reales; parametrizalas para probar sobre una copia.
    """
    global ultimo_resumen
    corpus_path, models_dir, reports_dir = Path(corpus_path), Path(models_dir), Path(reports_dir)
    textos = list(textos)
    if categorias is not None and len(categorias) != len(textos):
        raise ValueError("categorias debe tener la misma longitud que textos")

    existente = pd.read_csv(corpus_path)
    vistos = set(existente["text_original"])
    n_invalidos = n_duplicados = 0
    candidatos = []  # (texto, categoria)
    for i, t in enumerate(textos):
        if not isinstance(t, str) or not t.strip():
            n_invalidos += 1
            continue
        if t in vistos:  # duplicado exacto contra el corpus o contra el propio lote
            n_duplicados += 1
            continue
        vistos.add(t)
        cat = categorias[i] if categorias is not None else None
        cat = CATEGORIA_DESCONOCIDA if cat is None or pd.isna(cat) or not str(cat).strip() else str(cat).strip()
        candidatos.append((t, cat))

    lemas = preprocesar_lote([t for t, _ in candidatos], modo="lemma") if candidatos else []
    filas, n_cortos = [], 0
    ultimo = max(int(d.split("_")[1]) for d in existente["doc_id"])
    for (t, cat), lem in zip(candidatos, lemas):
        if len(lem) < MIN_TOKENS:
            n_cortos += 1
            continue
        filas.append({
            "doc_id": f"doc_{ultimo + 1 + len(filas):04d}",
            "category": cat,
            "titulo": " ".join(t.split()[:8]),
            "text_original": t,
            "text_norm": normalizar(t),
            "tokens_lemma": " ".join(lem),
            "tokens_stem": " ".join(stemizar(tokenizar(normalizar(t)))),
            "n_tokens": len(lem),
        })

    ultimo_resumen = {"recibidos": len(textos), "ingeridos": len(filas), "duplicados": n_duplicados,
                      "cortos": n_cortos, "invalidos": n_invalidos}
    if not filas:
        return []

    nuevas = pd.DataFrame(filas, columns=COLUMNAS_CORPUS)
    index_path = models_dir / "doc_index.csv"
    respaldo_corpus = corpus_path.read_bytes()
    respaldo_index = index_path.read_bytes() if index_path.exists() else None
    try:
        # Anade al final sin reescribir las filas existentes.
        if not respaldo_corpus.endswith(b"\n"):
            with open(corpus_path, "ab") as f:
                f.write(b"\n")
        nuevas.to_csv(corpus_path, mode="a", header=False, index=False)
        models_dir.mkdir(parents=True, exist_ok=True)
        nuevas[["doc_id", "category", "titulo"]].to_csv(
            index_path, mode="a", header=respaldo_index is None, index=False)
        construir_indices(corpus_path, models_dir, reports_dir)  # reconstruccion completa
    except Exception:
        corpus_path.write_bytes(respaldo_corpus)  # no dejar el corpus a medias
        if respaldo_index is not None:
            index_path.write_bytes(respaldo_index)
        raise

    if Path(models_dir).resolve() == MODELOS.resolve():
        from buscar import recargar
        recargar()  # invalida la cache de modelos del proceso
    return nuevas["doc_id"].tolist()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Agrega noticias nuevas al corpus y reconstruye los indices")
    ap.add_argument("--archivo", required=True, help="CSV con columna `text` y opcional `category`")
    a = ap.parse_args(argv)
    df = pd.read_csv(a.archivo)
    if "text" not in df.columns:
        ap.error("el CSV debe tener una columna `text`")
    cats = df["category"].where(df["category"].notna(), None).tolist() if "category" in df.columns else None
    ids = ingestar(df["text"].tolist(), cats)
    r = ultimo_resumen
    print(f"Recibidos: {r['recibidos']:,}  ingeridos: {r['ingeridos']:,}  duplicados: {r['duplicados']:,}  "
          f"cortos: {r['cortos']:,}  invalidos: {r['invalidos']:,}")
    print("doc_ids nuevos:", ", ".join(ids) if ids else "(ninguno)")


if __name__ == "__main__":
    main()

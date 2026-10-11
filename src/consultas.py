"""Etapa 6 (parte 1): conjunto de consultas de evaluacion.

100 consultas automaticas (20 por categoria, titulo del documento; ese documento se excluye de
su propio ranking) + 15 manuales (3 por categoria).

Uso (desde la raiz):  python src/consultas.py
Como modulo:          import consultas; df = consultas.generar_consultas()
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estilo_graficas import ORDEN_CATEGORIAS  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "data" / "processed" / "corpus_clean.csv"
SALIDA = RAIZ / "data" / "processed" / "consultas.csv"
COLUMNAS = ["query_id", "query", "categoria_esperada", "tipo", "doc_origen"]
N_POR_CATEGORIA = 20
SEMILLA = 42

CONSULTAS_MANUALES = {
    "business": ["interest rates central bank", "company profits shares", "oil price economy growth"],
    "entertainment": ["film award ceremony", "music album chart", "actor oscar nomination"],
    "politics": ["general election campaign", "prime minister blair", "tax plans government"],
    "sport": ["football match goal", "tennis open final", "rugby world cup"],
    "tech": ["mobile phone technology", "computer virus security", "video games console"],
}


def generar_consultas(ruta_corpus=CORPUS, salida=SALIDA, guardar=True) -> pd.DataFrame:
    """Construye (y por defecto guarda) data/processed/consultas.csv. Determinista (random_state=42)."""
    corpus = pd.read_csv(ruta_corpus, usecols=["doc_id", "category", "titulo"])
    filas = []
    for cat in ORDEN_CATEGORIAS:
        muestra = corpus[corpus["category"] == cat].sample(n=N_POR_CATEGORIA, random_state=SEMILLA)
        for r in muestra.sort_values("doc_id").itertuples():
            filas.append({"query": r.titulo, "categoria_esperada": cat, "tipo": "auto",
                          "doc_origen": r.doc_id})
    for i, r in enumerate(filas, start=1):
        r["query_id"] = f"auto_{i:03d}"
    n = 0
    for cat in ORDEN_CATEGORIAS:
        for q in CONSULTAS_MANUALES[cat]:
            n += 1
            filas.append({"query_id": f"manual_{n:02d}", "query": q, "categoria_esperada": cat,
                          "tipo": "manual", "doc_origen": ""})
    df = pd.DataFrame(filas)[COLUMNAS]
    assert df["query_id"].is_unique and len(df) == 115
    assert (df.groupby(["tipo", "categoria_esperada"]).size().unstack().loc["auto"] == 20).all()
    assert (df.groupby(["tipo", "categoria_esperada"]).size().unstack().loc["manual"] == 3).all()
    if guardar:
        Path(salida).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(salida, index=False, encoding="utf-8")
    return df


def main():
    df = generar_consultas()
    print(f"{len(df):,} consultas -> {SALIDA}")
    print(df.groupby(["tipo", "categoria_esperada"]).size().unstack())


if __name__ == "__main__":
    main()

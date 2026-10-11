"""Etapa 1 - descarga del corpus BBC News Classification.

Descarga `bbc-text.csv` desde el repositorio oficial, calcula su SHA-256 y
verifica su estructura. No limpia ni modifica el texto.

Uso: python src/descarga.py
Importable sin efectos secundarios: `from descarga import main, verificar`.
"""
import hashlib
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import pandas as pd

URL = "https://raw.githubusercontent.com/mdsohaib/BBC-News-Classification/master/bbc-text.csv"
REPO_GIT = "https://github.com/mdsohaib/BBC-News-Classification.git"
CLONE_DIR = Path("/tmp/bbc_repo")

RAIZ = Path(__file__).resolve().parents[1]
RUTA_CSV = RAIZ / "data" / "raw" / "bbc-text.csv"
RUTA_SHA = RAIZ / "data" / "raw" / "bbc-text.sha256"

TAMANO_MINIMO = 4_000_000  # bytes
FILAS_ESPERADAS = 2225
CATEGORIAS_ESPERADAS = {
    "sport": 511,
    "business": 510,
    "politics": 417,
    "tech": 401,
    "entertainment": 386,
}


def _descargar_url(destino: Path) -> None:
    with urllib.request.urlopen(URL, timeout=60) as resp:
        datos = resp.read()
    destino.write_bytes(datos)


def _descargar_git(destino: Path) -> None:
    if CLONE_DIR.exists():
        shutil.rmtree(CLONE_DIR)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_GIT, str(CLONE_DIR)],
        check=True,
    )
    shutil.copy(CLONE_DIR / "bbc-text.csv", destino)


def obtener_csv(ruta: Path = RUTA_CSV) -> str:
    """Asegura que el CSV exista. Devuelve 'ya existe', 'url' o 'git'."""
    if ruta.exists() and ruta.stat().st_size > TAMANO_MINIMO:
        print(f"ya existe: {ruta} ({ruta.stat().st_size:,} bytes)")
        return "ya existe"

    ruta.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"descargando {URL}")
        _descargar_url(ruta)
        return "url"
    except Exception as e:  # respaldo con git clone
        print(f"falló la descarga directa ({e}); intentando git clone")
        _descargar_git(ruta)
        return "git"


def calcular_sha256(ruta: Path = RUTA_CSV, salida: Path = RUTA_SHA) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    digest = h.hexdigest()
    salida.write_text(f"{digest}  {ruta.name}\n", encoding="utf-8")
    print(f"SHA-256: {digest}")
    return digest


def verificar(ruta: Path = RUTA_CSV) -> pd.DataFrame:
    """Lee el CSV, imprime shape/conteos/nulos y termina con sys.exit(1) si no cumple."""
    df = pd.read_csv(ruta)
    conteo = df["category"].value_counts()
    print(f"shape: {df.shape}")
    print("conteo por categoría:")
    print(conteo.to_string())
    print("nulos por columna:")
    print(df.isna().sum().to_string())

    if df.shape[0] != FILAS_ESPERADAS:
        sys.exit(
            f"ERROR: se esperaban {FILAS_ESPERADAS:,} filas y hay {df.shape[0]:,}."
        )
    if set(conteo.index) != set(CATEGORIAS_ESPERADAS):
        sys.exit(
            f"ERROR: categorías distintas a las esperadas {sorted(CATEGORIAS_ESPERADAS)}: "
            f"{sorted(conteo.index)}."
        )
    return df


def main() -> pd.DataFrame:
    obtener_csv()
    calcular_sha256()
    df = verificar()
    print("verificación OK")
    return df


if __name__ == "__main__":
    main()

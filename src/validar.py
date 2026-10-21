#!/usr/bin/env python
"""Ejecuta las verificaciones de checklist_calidad.yaml para una etapa.

Uso (desde la raíz del repo):
    python src/validar.py --etapa <etapa> [--checklist checklist_calidad.yaml]

Imprime una tabla `id | descripción | PASS/FAIL | detalle` y escribe
reports/validacion/<etapa>.json. Código de salida: 0 si todas las verificaciones
bloqueantes pasan, 1 si alguna falla (o si hay un error de uso).

Una verificación que lanza una excepción cuenta como FAIL con el detalle del error.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import traceback

import joblib
import numpy as np
import pandas as pd
import yaml

CMD_TIMEOUT = 600  # segundos por verificación tipo `comando`


# --------------------------------------------------------------------------
# Verificaciones: cada función recibe el dict `v` y devuelve (ok: bool, detalle: str)
# --------------------------------------------------------------------------
CONFIG = "proyecto.yaml"


def _fmt(n):
    return f"{n:,}" if isinstance(n, int) else str(n)


def chk_archivo_existe(v):
    ok = os.path.exists(v["ruta"])
    return ok, v["ruta"] + (" existe" if ok else " no existe")


def chk_csv_filas(v):
    n = len(pd.read_csv(v["ruta"]))
    lo, hi = v.get("min"), v.get("max")
    ok = (lo is None or n >= lo) and (hi is None or n <= hi)
    return ok, f"{_fmt(n)} filas (rango esperado [{_fmt(lo)}, {_fmt(hi)}])"


def chk_csv_columnas(v):
    # Lee solo la cabecera.
    cols = list(pd.read_csv(v["ruta"], nrows=0).columns)
    esperadas = list(v["columnas"])
    faltan = [c for c in esperadas if c not in cols]
    if faltan:
        return False, f"faltan columnas {faltan}; el CSV tiene {cols}"
    # Orden relativo: las columnas esperadas deben aparecer en ese orden.
    pos = [cols.index(c) for c in esperadas]
    if pos != sorted(pos):
        return False, f"columnas fuera de orden; esperado {esperadas}, encontrado {cols}"
    extra = [c for c in cols if c not in esperadas]
    det = f"columnas {esperadas} presentes y en orden"
    if extra:
        det += f" (columnas adicionales: {extra})"
    return True, det


def chk_csv_sin_nulos(v):
    df = pd.read_csv(v["ruta"])
    cols = list(v["columnas"])
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        return False, f"columnas inexistentes {faltan}"
    nulos = {c: int(df[c].isna().sum()) for c in cols}
    malos = {c: n for c, n in nulos.items() if n > 0}
    if malos:
        return False, f"nulos por columna: {malos}"
    return True, f"sin nulos en {cols}"


def chk_csv_sin_duplicados(v):
    df = pd.read_csv(v["ruta"])
    col = v["columna"]
    if col not in df.columns:
        return False, f"columna inexistente '{col}'"
    n = int(df[col].duplicated().sum())
    return n == 0, f"{_fmt(n)} duplicados en '{col}'"


def chk_json_rango(v):
    with open(v["ruta"], encoding="utf-8") as f:
        data = json.load(f)
    val = data
    for parte in str(v["clave"]).split("."):  # admite claves anidadas "a.b"
        val = val[parte]
    lo, hi = v.get("min"), v.get("max")
    ok = (lo is None or val >= lo) and (hi is None or val <= hi)
    return ok, f"{v['clave']} = {val} (rango esperado [{lo}, {hi}])"


def _entorno_comando():
    env = os.environ.copy()
    # Asegura que `python` resuelva al intérprete que ejecuta este script.
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    return env


def chk_comando(v):
    r = subprocess.run(
        v["cmd"], shell=True, capture_output=True, text=True,
        timeout=CMD_TIMEOUT, env=_entorno_comando(),
    )
    ok = r.returncode == 0
    det = f"código de salida {r.returncode}"
    if not ok:
        cola = (r.stderr.strip() or r.stdout.strip()).splitlines()[-3:]
        if cola:
            det += ": " + " | ".join(cola)
    return ok, det


def _cfg():
    """proyecto.yaml: todo lo que depende del corpus (vacío si el archivo no existe)."""
    if not os.path.exists(CONFIG):
        return {}
    with open(CONFIG, encoding="utf-8") as f:
        return _sin_auto(yaml.safe_load(f) or {})


def _sin_auto(x):
    """Los valores `auto` (todavía sin decidir) llegan a las verificaciones como None."""
    if isinstance(x, dict):
        return {k: _sin_auto(val) for k, val in x.items()}
    if isinstance(x, list):
        return [_sin_auto(val) for val in x]
    return None if x == "auto" else x


def chk_python(v):
    if "src" not in sys.path:
        sys.path.insert(0, "src")  # para que las expresiones puedan importar módulos del proyecto
    ns = {"os": os, "pd": pd, "np": np, "json": json, "joblib": joblib, "cfg": _cfg()}
    res = eval(v["expr"], ns)  # globals únicos: las comprensiones ven el namespace
    ok = res is True or (isinstance(res, (bool, np.bool_)) and bool(res))
    return ok, f"expr -> {res!r}"


TIPOS = {
    "archivo_existe": chk_archivo_existe,
    "csv_filas": chk_csv_filas,
    "csv_columnas": chk_csv_columnas,
    "csv_sin_nulos": chk_csv_sin_nulos,
    "csv_sin_duplicados": chk_csv_sin_duplicados,
    "json_rango": chk_json_rango,
    "comando": chk_comando,
    "python": chk_python,
}


def ejecutar(v):
    """Ejecuta una verificación; cualquier excepción => FAIL con el detalle."""
    tipo = v.get("tipo")
    try:
        if tipo not in TIPOS:
            return False, f"tipo de verificación desconocido: {tipo!r}"
        ok, det = TIPOS[tipo](v)
        return bool(ok), det
    except subprocess.TimeoutExpired:
        return False, f"timeout de {CMD_TIMEOUT}s"
    except Exception as e:  # noqa: BLE001 - intencional: no tumbar el script
        ultima = traceback.format_exc().strip().splitlines()[-1]
        return False, f"excepción {type(e).__name__}: {e} [{ultima}]"


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--etapa", required=True)
    ap.add_argument("--checklist", default="checklist_calidad.yaml")
    args = ap.parse_args()

    with open(args.checklist, encoding="utf-8") as f:
        checklist = yaml.safe_load(f)
    if args.etapa not in checklist:
        print(f"Etapa '{args.etapa}' no está en {args.checklist}. "
              f"Etapas: {list(checklist)}", file=sys.stderr)
        return 1

    filas = []
    for v in checklist[args.etapa]:
        ok, det = ejecutar(v)
        filas.append({
            "id": v.get("id"),
            "desc": v.get("desc", ""),
            "tipo": v.get("tipo"),
            "bloqueante": bool(v.get("bloqueante", False)),
            "resultado": "PASS" if ok else "FAIL",
            "detalle": det,
        })

    # Tabla en consola
    print(f"Etapa: {args.etapa}")
    print(f"{'id':<5}| {'descripción':<55}| {'res.':<5}| detalle")
    print("-" * 110)
    for r in filas:
        marca = "" if r["bloqueante"] else " (no bloqueante)"
        print(f"{r['id']:<5}| {r['desc'][:54]:<55}| {r['resultado']:<5}| {r['detalle']}{marca}")

    fallos_bloq = [r["id"] for r in filas if r["bloqueante"] and r["resultado"] == "FAIL"]
    fallos_menores = [r["id"] for r in filas if not r["bloqueante"] and r["resultado"] == "FAIL"]
    resultado = "PASS" if not fallos_bloq else "FAIL"
    print(f"\nResultado: {resultado}"
          + (f" | bloqueantes fallidas: {fallos_bloq}" if fallos_bloq else "")
          + (f" | no bloqueantes fallidas: {fallos_menores}" if fallos_menores else ""))

    os.makedirs("reports/validacion", exist_ok=True)
    salida = {
        "etapa": args.etapa,
        "fecha": dt.datetime.now().isoformat(timespec="seconds"),
        "resultado": resultado,
        "fallos_bloqueantes": fallos_bloq,
        "fallos_no_bloqueantes": fallos_menores,
        "verificaciones": filas,
    }
    with open(f"reports/validacion/{args.etapa}.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 0 if resultado == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

---
name: descarga
description: Descarga el corpus BBC News Classification (bbc-text.csv) desde el repositorio oficial de GitHub y verifica su integridad. Úsala en la etapa 1 del pipeline o cuando falte data/raw/bbc-text.csv.
---

# Descarga del corpus

## Datos conocidos del dataset

- Repositorio: `https://github.com/mdsohaib/BBC-News-Classification` (rama `master`).
- Archivo a usar: **`bbc-text.csv`** (≈5 MB). El repo también trae notebooks; no los uses.
- Columnas: `category`, `text`.
- Filas esperadas: **2,225**.
- Categorías esperadas (5): `sport` 511, `business` 510, `politics` 417, `tech` 401, `entertainment` 386.
- El texto ya viene en minúsculas y casi sin puntuación; el título está pegado al inicio del cuerpo, sin separador.
- Contiene **99 textos duplicados** (se quitan en `limpieza`, no aquí).

## Pasos

1. Crea `src/descarga.py` con este comportamiento:
   - URL directa: `https://raw.githubusercontent.com/mdsohaib/BBC-News-Classification/master/bbc-text.csv`
   - Descarga con `urllib.request` (sin dependencias extra) a `data/raw/bbc-text.csv`.
   - Si la descarga falla, intenta como respaldo: `git clone --depth 1 https://github.com/mdsohaib/BBC-News-Classification.git /tmp/bbc_repo` y copia `bbc-text.csv`.
   - Si el archivo ya existe y su tamaño es > 4,000,000 bytes, no lo vuelvas a descargar (imprime `ya existe`).
   - Calcula el SHA-256 del archivo y guárdalo en `data/raw/bbc-text.sha256`.
2. Agrega al final del script una verificación que imprima:
   - `shape` del DataFrame,
   - conteo por categoría,
   - número de nulos por columna.
   Si las filas ≠ 2,225 o las categorías ≠ las 5 esperadas, termina con `sys.exit(1)` y un mensaje claro.
3. Ejecuta `python src/descarga.py`.
4. Escribe `reports/descarga.md` con: URL usada, fecha, SHA-256, filas, tabla de conteo por categoría (números con separador de miles).

## Salidas

- `data/raw/bbc-text.csv` (ignorado por git; se regenera con el script)
- `data/raw/bbc-text.sha256`
- `src/descarga.py`
- `reports/descarga.md`

## No hagas

- No limpies ni modifiques el texto.
- No subas el CSV al repositorio.

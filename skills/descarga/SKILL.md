---
name: descarga
description: Obtiene el corpus del proyecto (un CSV con una columna de texto y otra de categoría) desde la URL indicada en proyecto.yaml y verifica su integridad. Úsala en la etapa 1 del pipeline o cuando falte el CSV en data/raw/.
---

# Descarga del corpus

Todo lo específico del dataset está en la sección `datos` de `proyecto.yaml`: `url`, `repo_respaldo`, `archivo_en_repo`, `ruta_raw`, `tamano_minimo_bytes`, `columna_texto`, `columna_categoria`, `filas_esperadas`, `categorias` (nombre → documentos esperados), `duplicados_esperados` y `notas`. Léelo antes de empezar y no copies esos valores en el código.

## Pasos

1. Crea `src/descarga.py`, con la lógica en funciones (`main()`, `verificar()`) y sin efectos al importarse:
   - Descarga `datos.url` con `urllib.request` (sin dependencias extra) a `datos.ruta_raw`.
   - Si la descarga falla y hay `datos.repo_respaldo`, clona con `git clone --depth 1 <repo_respaldo>` en un directorio temporal y copia `datos.archivo_en_repo`.
   - Si el archivo ya existe y su tamaño supera `datos.tamano_minimo_bytes`, no lo vuelvas a descargar (imprime `ya existe`). Esto permite usar una copia local del usuario: colócala en `datos.ruta_raw` antes de ejecutar.
   - Calcula el SHA-256 del archivo y guárdalo junto al CSV, con el mismo nombre y extensión `.sha256`.
2. Agrega al final del script una verificación que imprima:
   - `shape` del DataFrame,
   - conteo por categoría (`datos.columna_categoria`),
   - número de nulos por columna.
   Si faltan las columnas de texto o categoría, si las filas ≠ `datos.filas_esperadas` o si las categorías no son exactamente las claves de `datos.categorias`, termina con `sys.exit(1)` y un mensaje claro. Si esos valores esperados están en `null` (todavía no se conocen), no los compruebes: imprime los valores reales para que el usuario los registre en `proyecto.yaml`.
3. Si el corpus no viene como un CSV (carpetas de `.txt` por categoría, JSON, varios archivos), conviértelo en este mismo script a un único CSV con una columna de texto y otra de categoría, guárdalo en `datos.ruta_raw` y documenta la conversión en el reporte.
4. Ejecuta `python src/descarga.py`.
5. Escribe `reports/descarga.md` con: URL usada (o "copia local" si no se descargó), fecha, SHA-256, filas, tabla de conteo por categoría (números con separador de miles).

## Salidas

- El CSV en `datos.ruta_raw` (ignorado por git; se regenera con el script)
- El `.sha256` junto al CSV
- `src/descarga.py`
- `reports/descarga.md`

## No hagas

- No limpies ni modifiques el texto.
- No subas el CSV al repositorio.
- Si el dataset trae otros archivos (notebooks, versiones alternativas), no los uses.

---
name: descarga
description: Obtiene el corpus de textos desde una URL, un archivo o una carpeta, detecta su formato y sus columnas, lo convierte a un CSV estándar y verifica su integridad. Úsala en la etapa 1 del pipeline o cuando falte el CSV en data/raw/.
---

# Obtención del corpus

Lee la sección `datos` de `proyecto.yaml`. Respeta lo que esté fijado y decide lo que esté en `auto` con las reglas de abajo; escribe cada decisión de vuelta en `proyecto.yaml` y añádela a `decisiones` con su razón (ver la skill `orquestador`).

## Decide según los datos

### Origen

| Si en `datos` hay… | Haz |
|---|---|
| `url` | Descarga con `urllib.request` a `data/raw/original/`. Si falla y hay `repo_respaldo`, clona con `git clone --depth 1` en un directorio temporal y copia `archivo_en_repo`. |
| `ruta_local` (archivo o carpeta) | Úsala tal cual; no la modifiques ni la muevas. |
| nada | Detente y pregunta al usuario dónde están los datos. |

Si el archivo ya existe en destino y supera `tamano_minimo_bytes` (si es `auto`, 1 KB), no lo vuelvas a descargar.

### Formato

| Si el origen es… | Lee con |
|---|---|
| `.csv` / `.tsv` / `.txt` tabular | `pandas.read_csv` detectando separador (`csv.Sniffer`) y codificación (prueba `utf-8`, luego `latin-1`) |
| `.json` / `.jsonl` | `pandas.read_json` (`lines=True` para `.jsonl`) |
| `.xlsx` / `.xls` | `pandas.read_excel` (primera hoja, salvo que solo otra tenga texto) |
| `.parquet` | `pandas.read_parquet` |
| `.zip` / `.tar.gz` | Descomprime en `data/raw/original/` y vuelve a aplicar esta tabla |
| Carpeta con subcarpetas de `.txt` | Un documento por archivo; la **categoría es el nombre de la subcarpeta**. Si el archivo tiene una primera línea corta (≤ 15 palabras) seguida de línea en blanco, es el título |
| Carpeta de `.txt` sin subcarpetas | Un documento por archivo, sin categoría |
| Un `.txt` con un documento por línea | Un documento por línea, sin categoría |

Registra en el reporte cuántos archivos o filas no se pudieron leer y por qué.

### Columnas (si `columna_texto`, `columna_categoria` o `columna_titulo` están en `auto`)

1. **Texto**: la columna de tipo cadena con mayor mediana de palabras, siempre que esa mediana sea ≥ 5 y que al menos 90% de sus valores sean distintos. Si hay columnas de título y de cuerpo separadas, el texto es el cuerpo y el título va a `columna_titulo`.
2. **Título**: una columna de cadenas cortas (mediana ≤ 15 palabras), casi siempre distinta, cuyo nombre o contenido sugiera título (`title`, `titulo`, `headline`, `subject`…). Si no existe, `columna_titulo: null` (la limpieza usará las primeras palabras del texto).
3. **Categoría**: una columna con entre 2 y 50 valores distintos, donde la categoría más pequeña tenga al menos 2% de los documentos, y cuyo nombre o valores sugieran una etiqueta (`category`, `label`, `class`, `topic`, `section`…). Descarta identificadores, fechas y columnas numéricas continuas.
   - Si ninguna cumple: `columna_categoria: null`. El pipeline sigue sin categorías (la evaluación usará búsqueda de ítem conocido).
   - Si hay más de una candidata y no hay una evidente por el nombre, pregunta al usuario.
4. Una columna de identificador original, si existe, se conserva como `id_original`.

### CSV estándar

Escribe `datos.ruta_raw` (si es `auto`, `data/raw/corpus.csv`) con las columnas originales detectadas, sin modificar el texto. Si el origen ya era un CSV, el estándar puede ser el mismo archivo.

## Verificación

Al final de `src/descarga.py`, imprime: `shape`, conteo por categoría (si hay), nulos por columna, documentos con texto vacío. Termina con `sys.exit(1)` y un mensaje claro si:
- no hay columna de texto, o el corpus tiene menos de 50 documentos con texto;
- `datos.filas_esperadas` o `datos.categorias` están fijados (no `auto` ni `null`) y no coinciden con lo leído.

Si esos valores estaban en `auto`, escribe en `proyecto.yaml` los observados (`filas_esperadas`, `categorias` con sus conteos) para que las etapas siguientes y la validación los usen.

## Pasos

1. Crea `src/descarga.py` con la lógica en funciones (`main()`, `verificar()`), sin efectos al importarse, que aplique las reglas de arriba y lea todo de `proyecto.yaml`.
2. Calcula el SHA-256 del archivo de `datos.ruta_raw` y guárdalo junto a él con extensión `.sha256`.
3. Ejecuta `python src/descarga.py`.
4. Escribe `reports/descarga.md` con: origen (URL, archivo local o carpeta), formato detectado y cómo se convirtió, fecha, SHA-256, filas, columnas elegidas para texto/título/categoría y por qué, tabla de conteo por categoría (números con separador de miles).

## Salidas

- `datos.ruta_raw` y su `.sha256` (ignorados por git; se regeneran con el script)
- `src/descarga.py`
- `reports/descarga.md`
- `proyecto.yaml` actualizado (sección `datos` y `decisiones`)

## No hagas

- No limpies ni modifiques el texto.
- No subas los datos al repositorio.
- No uses archivos accesorios del origen (notebooks, versiones alternativas) salvo que sean el único lugar donde está el texto.

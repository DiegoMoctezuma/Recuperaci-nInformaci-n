# Validación de calidad: etapa `descarga`

- Fecha: 2026-10-11
- Resultado: **PASS**
- Comando: `conda run -n bbc-ir python src/validar.py --etapa descarga` (código de salida 0)
- Entorno: conda `bbc-ir`, Python 3.11.17, pandas 3.0.6
- Detalle máquina: `reports/validacion/descarga.json`

## Verificaciones del checklist

| id | Descripción | Bloqueante | Resultado | Detalle |
|---|---|---|---|---|
| D1 | CSV descargado | sí | PASS | `data/raw/bbc-text.csv` existe |
| D2 | 2,225 filas | sí | PASS | 2,225 filas |
| D3 | columnas category y text | sí | PASS | `['category', 'text']` en orden |
| D4 | 5 categorías esperadas | sí | PASS | conjunto igual a {business, entertainment, politics, sport, tech} |
| D5 | hash registrado | no | PASS | `data/raw/bbc-text.sha256` existe |
| D6 | reporte de descarga | sí | PASS | `reports/descarga.md` existe |

## Verificaciones adicionales ejecutadas

| Verificación | Resultado | Evidencia |
|---|---|---|
| `conda run -n bbc-ir python src/descarga.py` sale con código 0 | PASS | imprime `ya existe: ... (5,059,719 bytes)`, SHA-256, shape `(2225, 2)`, conteos, nulos y `verificación OK`; exit 0 |
| SHA-256 recalculado (`shasum -a 256`) = `bbc-text.sha256` = `reports/descarga.md` | PASS | los tres: `e7652d6aa0fa92b2d02c6a992ebda82281041f83e7c2a92ae6e9c1c444981a8d` |
| Tamaño del reporte (5,059,719 bytes) = `stat` del CSV | PASS | coincide |
| Filas y conteos del reporte = CSV | PASS | 2,225 filas; sport 511, business 510, politics 417, tech 401, entertainment 386; suma 2,225 |
| Nulos (0/0) y duplicados de texto (99) del reporte = CSV | PASS | `isna().sum()` = 0/0; `text.duplicated().sum()` = 99 |
| Separador de miles en el reporte | PASS | "2,225", "5,059,719" |
| CSV ignorado por git | PASS | `git check-ignore`: `.gitignore:1:data/raw/` |

## Revisión cualitativa (contra skills/descarga/SKILL.md)

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| Código en `src/` y corre desde la raíz sin pasos manuales | Sí | `src/descarga.py`; rutas relativas a la raíz vía `Path(__file__)`; ejecutado con éxito |
| URL directa, `urllib.request`, destino `data/raw/bbc-text.csv` | Sí | `URL` raw de mdsohaib/master; `_descargar_url` con `urllib.request.urlopen` |
| Respaldo `git clone --depth 1 ... /tmp/bbc_repo` y copia de `bbc-text.csv` | Sí | `_descargar_git` (la rama de respaldo y la de descarga no se ejecutaron en esta corrida; solo se revisó el código) |
| Omite descarga si existe y tamaño > 4,000,000 bytes, imprime `ya existe` | Sí | `TAMANO_MINIMO = 4_000_000`, estricto `>`; salida observada |
| SHA-256 guardado en `data/raw/bbc-text.sha256` | Sí | formato `hash  archivo`, compatible con `shasum -c` |
| Verificación final: shape, conteo por categoría, nulos; `sys.exit(1)` si filas != 2,225 o categorías distintas | Sí | `verificar()` imprime los tres y sale con mensaje claro |
| Reporte con URL, fecha, SHA-256, filas y tabla de conteo con miles | Sí | todos presentes |
| No limpia ni modifica el texto; CSV no subido | Sí | solo `pd.read_csv` de lectura; CSV ignorado por git |

## Advertencias

1. Desviación acordada con el usuario (no es FAIL): el CSV ya existía localmente, por lo que la descarga por URL y el respaldo con `git clone` no se ejercitaron; solo se revisó el código. El reporte lo declara explícitamente.
2. Menor: el reporte incluye una fecha pero no la hora; la skill solo pide fecha. Sin impacto.
3. Menor: `src/descarga.py` y `reports/descarga.md` siguen sin seguimiento en git (se espera que el orquestador los confirme).

## Instrucciones de corrección

No aplica (PASS).

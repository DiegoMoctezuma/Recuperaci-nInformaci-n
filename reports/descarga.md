# Reporte de descarga

- **Fecha:** 2026-10-11
- **URL oficial:** https://raw.githubusercontent.com/mdsohaib/BBC-News-Classification/master/bbc-text.csv (repositorio: https://github.com/mdsohaib/BBC-News-Classification, rama `master`)
- **Origen usado:** copia local ya existente en `data/raw/bbc-text.csv` (mismo archivo del repositorio oficial). No se descargó de internet; el script tomó la rama `ya existe`.
- **Tamaño:** 5,059,719 bytes
- **SHA-256:** `e7652d6aa0fa92b2d02c6a992ebda82281041f83e7c2a92ae6e9c1c444981a8d` (guardado en `data/raw/bbc-text.sha256`)
- **Columnas:** `category`, `text`
- **Filas:** 2,225 (coincide con lo esperado)
- **Nulos:** 0 en `category`, 0 en `text`
- **Duplicados:** 99 textos duplicados (se eliminan en la etapa `limpieza`, no aquí)

## Conteo por categoría

| Categoría | Documentos |
|---|---:|
| sport | 511 |
| business | 510 |
| politics | 417 |
| tech | 401 |
| entertainment | 386 |
| **Total** | **2,225** |

## Verificación

Filas = 2,225 y las 5 categorías esperadas con los conteos esperados: **OK**. El texto no fue limpiado ni modificado.

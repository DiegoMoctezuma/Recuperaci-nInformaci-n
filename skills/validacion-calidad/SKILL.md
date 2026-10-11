---
name: validacion-calidad
description: Revisa la calidad de una etapa del pipeline BBC contra checklist_calidad.yaml y decide PASS o FAIL; si falla, exige repetir la etapa con la corrección concreta antes de avanzar. Úsala después de cada etapa o cuando el usuario pida "validar", "revisar calidad" o "¿podemos avanzar?".
---

# Validación de calidad (compuerta entre etapas)

Eres un revisor estricto. Tu decisión se basa en **verificaciones ejecutadas**, no en tu impresión del código. Una etapa solo pasa si todas las verificaciones `bloqueante: true` pasan.

## Archivos

- `checklist_calidad.yaml` (en la carpeta de esta skill; cópialo a la raíz del repo la primera vez): verificaciones por etapa.
- `src/validar.py`: script que ejecuta las verificaciones. Si no existe, créalo (paso 1).
- `estado/progreso.json`: donde escribes el resultado.
- `reports/validacion/<etapa>.md`: informe de cada validación.

## Paso 1 — Crear `src/validar.py` (solo la primera vez)

- Uso: `python src/validar.py --etapa <etapa>`.
- Lee `checklist_calidad.yaml` y ejecuta cada verificación de la etapa según su `tipo`:
  - `archivo_existe`: `os.path.exists(ruta)`.
  - `csv_filas`: filas del CSV entre `min` y `max`.
  - `csv_columnas`: el CSV contiene exactamente/al menos las columnas listadas.
  - `csv_sin_nulos`: sin nulos en las columnas listadas.
  - `csv_sin_duplicados`: sin duplicados en la columna indicada.
  - `json_rango`: el valor de `clave` en el JSON está entre `min` y `max`.
  - `comando`: ejecuta `cmd`; pasa si el código de salida es 0.
  - `python`: evalúa una expresión Python corta (`expr`) que debe dar `True`; dispone de `os`, `pd`, `np`, `json`, `joblib`. Ejecuta todo desde la raíz del repo.
- Imprime una tabla `id | descripción | PASS/FAIL | detalle` y escribe `reports/validacion/<etapa>.json`.
- Sale con código 0 si todas las bloqueantes pasan, 1 si no.

## Paso 2 — Validar la etapa

1. Ejecuta `python src/validar.py --etapa <etapa>`.
2. Revisión cualitativa adicional (no sustituye al script), responde sí/no con evidencia:
   - ¿El código está en `src/` y corre desde la raíz sin pasos manuales?
   - ¿Las rutas y parámetros coinciden con el SKILL.md de la etapa?
   - ¿El reporte `.md` de la etapa existe y sus números coinciden con los JSON?
   - ¿Formato: miles con coma, porcentajes con 2 decimales?
   Un "no" aquí es FAIL solo si contradice el SKILL.md de la etapa; si es menor, ponlo como advertencia.
3. Escribe `reports/validacion/<etapa>.md`: fecha, resultado, tabla de verificaciones, advertencias, y (si falla) **instrucciones de corrección**.

## Paso 3 — Decidir y registrar

- **PASS**: en `estado/progreso.json` pon `estado: "PASS"` y `notas: ""` (o las advertencias).
- **FAIL**: pon `estado: "FAIL"`, incrementa `intentos` en 1 y escribe en `notas` la corrección concreta, en imperativo y verificable. Ejemplo bueno: `"corpus_clean.csv tiene 2,225 filas; aplica drop_duplicates(subset='text') antes de asignar doc_id"`. Ejemplo malo: `"revisar los datos"`.
- Si `intentos` llega a 3, pon `estado: "BLOQUEADA"` y en `notas` resume los 3 fallos para que un humano decida.

## Reglas

- Nunca marques PASS si el script salió con código 1.
- Nunca edites los archivos de la etapa para que pase: tú solo validas; la corrección la hace la skill de la etapa en el reintento.
- Nunca relajes un umbral del checklist sin que el usuario lo pida explícitamente; si lo pide, registra el cambio en el informe.

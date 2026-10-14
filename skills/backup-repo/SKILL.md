---
name: backup-repo
description: Respalda el progreso en el repositorio compartido del equipo (commit + push) después de cada etapa validada o cuando el usuario pida guardar/respaldar/subir avances. Registra el commit en estado/progreso.json.
---

# Respaldo en el repositorio compartido

Objetivo: que ningún avance viva solo en una computadora y que cualquier integrante pueda retomar desde el último `PASS`.

## Convenciones del equipo

- Repositorio remoto: `origin` (GitHub del equipo).
- Rama de trabajo: `<nombre>/<etapa>`, p. ej. `rafa/indices`. Obtén `<nombre>` de `git config user.name` (primer nombre en minúsculas, sin acentos).
- `main` solo recibe etapas con `PASS`, vía merge (ver paso 6).
- Formato del mensaje de commit:
  ```
  <etapa>: <PASS|WIP|FAIL> — <resumen de 1 línea con un número clave>

  Archivos: <lista corta>
  Validación: <resultado de validacion-calidad o "sin validar">
  ```
  Ejemplo: `limpieza: PASS — 12,345 docs tras quitar 87 duplicados`

## Pasos

1. Verifica que estás en un repo git (`git rev-parse --is-inside-work-tree`). Si no, detente y pide al usuario la URL del repo; no crees uno nuevo por tu cuenta.
2. Verifica que `.gitignore` excluye `data/raw/`, `models/*.pkl`, `models/*.npy`, `models/*.model`. Si un archivo a subir pesa > 50 MB, no lo agregues y avisa.
3. Cambia o crea la rama de la etapa: `git switch <nombre>/<etapa>` o `git switch -c <nombre>/<etapa>`.
4. `git add -A` y revisa `git status --short`. Si no hay cambios, no hagas commit vacío: termina y repórtalo.
5. Commit con el formato de arriba y luego:
   ```
   git pull --rebase origin <rama> (si la rama existe en remoto)
   git push -u origin <rama>
   ```
6. Si la etapa tiene `PASS`:
   ```
   git switch main
   git pull --rebase origin main
   git merge --no-ff <nombre>/<etapa> -m "merge <etapa>: PASS"
   git push origin main
   ```
7. Actualiza `estado/progreso.json` en esa etapa: `commit` (hash corto), `fecha` (ISO 8601), `autor`. Haz un commit pequeño `estado: <etapa> respaldada` y push.
8. Reporta: rama, hash corto, archivos incluidos.

## Si algo falla

- **Conflicto en rebase o merge**: detente, ejecuta `git rebase --abort` o `git merge --abort`, muestra los archivos en conflicto y pide al usuario que decida. No resuelvas conflictos de código ajeno por tu cuenta.
- **Conflicto solo en `estado/progreso.json`**: combina a mano conservando, por etapa, la entrada con la `fecha` más reciente.
- **Push rechazado por permisos**: avisa; no cambies el remoto.

## Nunca

- `git push --force` ni `--force-with-lease`.
- `git reset --hard` sobre trabajo no respaldado.
- Subir datos crudos, credenciales o archivos `.env`.

## Automatizarlo (opcional, recomendado)

Para respaldo constante en Claude Code, agrega en `.claude/settings.json` un hook `Stop` que haga un commit WIP al final de cada turno:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command",
        "command": "git add -A && git diff --cached --quiet || git commit -m \"wip: autosave $(date +%Y-%m-%dT%H:%M)\" && git push -q || true" } ] }
    ]
  }
}
```

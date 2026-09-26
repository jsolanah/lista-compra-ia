---
description: Analiza cambios y crea un commit Conventional Commits en español
agent: build
---

Analiza el estado del repositorio y genera un commit Conventional Commits.

## Contexto del repositorio

Estado actual:
!`git status --short`

Diff staged:
!`git diff --staged`

Diff sin stage (resumido, máx. 200 líneas):
!`git diff -- . | head -200`

Histórico reciente (para imitar el estilo):
!`git log --oneline -15`

## Pasos

1. **Audita secretos en el contenido a commitear.** Busca en el diff y en los archivos no versionados: claves `AIza*` (Gemini), `ctx7sk-*` (Context7), `service_role`, `SUPABASE_SECRET_KEY`, `sk-` de OpenAI, `ghp_`/`github_pat_` de GitHub, cadenas `eyJ` (JWT). Si detectas alguna, **NO hagas commit**: enuméramelas con archivo y línea, sugiere `git add <archivo>`, añade el patrón a `.gitignore` si corresponde, y detente.

2. **Verifica los tests** antes de commitear:
!`python -m unittest discover -s tests 2>&1 | tail -20`
   Si fallan, no commitear hasta que se resuelvan o el usuario lo autorice explícitamente.

3. **Stagea solo lo que pertenece al cambio.** No uses `git add -A` por defecto. Si hay archivos ajenos al cambio (logs, `__pycache__`, `.db`, `.env.local`, `.vscode`), déjalos fuera y menciónalos. Nunca stagees `.env`, `.env.local`, `data/*.db` ni `node_modules`.

4. **Redacta el mensaje** siguiendo Conventional Commits, en **español**, en minúsculas, con el estilo ya presente en el histórico:

   ```
   <tipo>(<ámbito>): <descripción en imperativo>
   ```

   Tipos válidos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

   Reglas:
   - Una sola línea, ≤ 72 caracteres.
   - Sin punto final.
   - Describe *qué* cambia y *por qué*, no el proceso.
   - Ámbito opcional: `auth`, `pdf`, `cache`, `ui`, `config`, `deps`.
   - Añade cuerpo (separado por línea en blanco) solo si el cambio necesita contexto: **por qué**, no **qué** (el diff ya lo dice). Usa viñetas y ancho de 80.
   - Si el commit rompe la API pública o cambia el esquema de BD, añade sección `BREAKING CHANGE:`.

   Ejemplos del estilo de este repo:
   - `fix: ocultar hash interno de las dietas`
   - `feat: abrir menú móvil desde el aviso principal`
   - `test: añadir suite de pruebas para caché e historial`

5. **Muestra el plan antes de ejecutar.** Presenta el mensaje propuesto y la lista exacta de archivos staged, y espera confirmación.

6. **Commitea** con el mensaje aprobado, en un único commit salvo que el usuario pida dividirlo.

## Prohibido

- `--force`, `--force-with-lease`, `--no-verify`, `--amend` (salvo petición explícita)
- Escribir en `git config` o modificar hooks
- `git push` (solo commit; el push lo decide el usuario)
- Commits de trabajo vacío
- Incluir secretos o archivos de entorno

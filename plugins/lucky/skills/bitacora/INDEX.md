# Bitácora — INDEX (catálogo por síntoma)

> El ÚNICO punto de entrada. Ordenado por `usos` (lo que más duele, arriba).
> ≤1 pantalla: si pasa de ~40 filas, podá lo STALE o partí por tipo. El agente
> matchea lo que OBSERVA contra la columna **SÍNTOMA** y abre SOLO esa entrada
> (lazy). NO volcar este archivo entero al contexto.
>
> Tipos: **GAP** (hueco de spec mid-task) · **GREP** (re-derivar / navegación
> ciega) · **DRIFT** (docs↔código / config / arquitectura) · **FALSO-VERDE**
> (el verde miente). Estado: CANDIDATE → LIVE → STALE/SUPERSEDED/RETIRED.

| SÍNTOMA OBSERVABLE (lo que ves) | TIPO | ACCIÓN (1 línea) | ENTRADA | validated_on | usos | estado |
|---|---|---|---|---|---|---|
| El test/verify pasa en verde pero al auditar el código un check OBLIGATORIO está tras un `if` que lo desactiva en silencio | FALSO-VERDE | Auditá lo que el CÓDIGO hace, no lo que el comentario promete; confirmá fail-closed | [DRIFT-001](entries/DRIFT-001.md) | 2026-06-13 | 2 | CANDIDATE |
| Vas a grep/glob ciego buscando dónde vive un flujo, o preguntás "¿dónde está X?" sin mirar el mapa del repo | GREP | Pará de grepear; abrí el MAPA (Key Files ≤5); escalá ripgrep→ast-grep→LSP | [GREP-001](entries/GREP-001.md) | 2026-06-28 | 1 | CANDIDATE |
| Aparece una incógnita técnica con >2 ramas a mitad de tarea y no hay ADR que la resuelva | GAP | PARÁ; spike timebox 2h que responde UNA pregunta; recién con evidencia abrí el Crisol | [GAP-001](entries/GAP-001.md) | 2026-06-28 | 1 | CANDIDATE |
| Tras un redeploy, loguear al portal da `{"detail":"csrf token invalid"}` (403) y el hard-reload no recupera (solo pestaña nueva) | DRIFT | PRG: ante CSRF inválido en form → **303** a `GET /login?expired=1` (cookie+token frescos); 403 JSON solo para API | [DRIFT-002](entries/DRIFT-002.md) | 2026-06-26 | 1 | LIVE |

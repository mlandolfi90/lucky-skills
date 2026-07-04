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
| El test/verify pasa en verde pero al auditar el código un check OBLIGATORIO está tras un `if` que lo desactiva en silencio | FALSO-VERDE | Auditá lo que el CÓDIGO hace, no lo que el comentario promete; confirmá fail-closed | [DRIFT-001](entries/DRIFT-001.md) | 2026-07-02 | 3 | LIVE |
| El PaaS dice `healthy` pero la app no responde de afuera (`curl` → 000/timeout, cuelgue no 503) tras un reload del proxy | FALSO-VERDE/DRIFT | Fijá `traefik.docker.network` a LITERAL (no `${VAR:-}`) + redeploy; "Restart Proxy" solo maquilla (deja la bomba armada) | [DRIFT-003](entries/DRIFT-003.md) | 2026-07-01 | 2 | LIVE |
| El verificador de deploy lee el sha/tag del panel del PaaS, no coincide con lo pusheado y declara FAIL — pero la app viva YA sirve el cambio | DRIFT | Metadata Coolify pull-based queda CONGELADA: provenance FUNCIONAL (endpoint de versión / marcadores vivos + `git log -S`), jamás el panel | [DRIFT-006](entries/DRIFT-006.md) | 2026-07-03 | 2 | LIVE |
| El deploy no sale en >10 min: último run `success` con deploy `skipped`, los anteriores `cancelled`, sha vivo = viejo | GAP | Concurrency canceló el run del fix y el HEAD docs-only no gatilla deploy → `workflow_dispatch` sobre el branch (deploya siempre); nada de commits dummy | [GAP-003](entries/GAP-003.md) | 2026-07-03 | 2 | LIVE |
| Tras un redeploy, loguear al portal da `{"detail":"csrf token invalid"}` (403) y el hard-reload no recupera (solo pestaña nueva) | DRIFT | PRG: ante CSRF inválido en form → **303** a `GET /login?expired=1` (cookie+token frescos); 403 JSON solo para API | [DRIFT-002](entries/DRIFT-002.md) | 2026-06-26 | 1 | LIVE |
| Agregaste un workflow de CI con `schedule:` (cron) y jamás corre — 0 runs, sin error visible | GAP | Los cron de Actions corren SOLO desde la rama default; repo dev-only → el periódico va a un scheduler externo, NO a Actions | [GAP-002](entries/GAP-002.md) | 2026-07-01 | 1 | LIVE |
| Tras un deploy, una acción normal de la UI (ej. "Guardar") produce un efecto masivo/destructivo sin error visible — el server es la última versión | DRIFT | La pestaña vieja manda el payload del contrato viejo: exponé versión de build + detección en el poll + banner "Actualizar ahora / Luego" que bloquea writes | [DRIFT-004](entries/DRIFT-004.md) | 2026-07-03 | 1 | LIVE |
| Tests verdes en local pero el stage `test` del CI muere en collection con `ModuleNotFoundError` de un módulo NUEVO en TODOS los test modules | DRIFT | El COPY enumerado del Dockerfile no copia el archivo nuevo: sumalo a la línea COPY (ninguna gimnasia de imports lo arregla) | [DRIFT-005](entries/DRIFT-005.md) | 2026-07-03 | 1 | LIVE |
| Un endpoint "documentado" del servicio da 404 aunque el servicio está sano (ej. cost map de litellm) | GREP | La verdad es el DEPLOYADO, no la doc: consultá su openapi/código de esa versión (litellm del stack: `GET /public/litellm_model_cost_map`, sin auth) | [GREP-002](entries/GREP-002.md) | 2026-07-03 | 1 | LIVE |
| La capacidad de un modelo (ventana/output) viene de un agregador o tabla de memoria y aparece desactualizada, faltante o contradictoria | GAP | El proveedor SÍ la expone (era semántica: Anthropic `GET /v1/models` → `max_input_tokens`/`max_tokens`); la sonda vive en el handler con SUS creds, precedencia proveedor > agregador > 422 | [GAP-004](entries/GAP-004.md) | 2026-07-03 | 1 | LIVE |
| Docker Desktop: cartel "An unexpected error occurred" al arrancar, nombra un socket bajo AppData ("cannot be accessed"), y reintentar reproduce el crash | GAP | Matar procesos + wsl --shutdown + RENOMBRAR `Dockerun` y `docker-secrets-engine`; fix real = ≥4.80. JAMÁS "Reset to factory defaults" | [GAP-005](entries/GAP-005.md) | 2026-07-03 | 1 | LIVE |
| Tras aceptar una variante de Live Mode la UI se ve bien y compila, pero el diff perdió ramas del componente (botones condicionales, portals) | FALSO-VERDE | Variante = componente COMPLETO; diff post-accept contra el original + typecheck | [FALSO-VERDE-001](entries/FALSO-VERDE-001.md) | 2026-07-03 | 1 | LIVE |
| Script ESM ajeno en contenedor pide "npm install X" con X ya instalado (NODE_PATH ignorado), o Chrome muere "No usable sandbox" | GREP | Copiar el script junto al node_modules de la imagen + `--cap-add=SYS_ADMIN`; bind 127.0.0.1 → proxy TCP interno | [GREP-003](entries/GREP-003.md) | 2026-07-03 | 1 | LIVE |

## [DRIFT-003] El PaaS dice "healthy" pero la app no responde de afuera (curl → 000/timeout) tras un reload del proxy

- **TIPO:** FALSO-VERDE (el healthcheck miente) + DRIFT (label de red del reverse-proxy)
- **SÍNTOMA (lo observable, NO la causa):** Una app detrás del reverse-proxy (Traefik) en el PaaS
  (Coolify) queda inalcanzable desde afuera — `curl` público → **000 / timeout (cuelgue, NO 503)** —
  mientras el PaaS y **todos** los healthchecks la reportan `running:healthy`. Suele dispararse tras un
  **reload del proxy** causado por churn de OTRO stack (no por el deploy propio).
- **CAUSA-RAÍZ (1 línea):** el label `traefik.docker.network: ${VAR:-}` NO fue interpolado por el PaaS
  → el proxy quedó sin hint de red válido → auto-seleccionó (no-determinista en cada reload) una IP de
  una red a la que el proxy NO está conectado → el connect al backend cuelga. Bomba latente: cada reload la re-arma.
- **ACCIÓN (pasos, máx 7):**
  1. Diagnóstico: **000/hang ≠ 503**. 503 = sin backend/router; **hang = el proxy TIENE IP de backend
     pero no la alcanza** → eligió la red inalcanzable.
  2. Probá la app **directo desde el host** (bypass proxy): si da 200, la app está sana → el problema es el ruteo.
  3. Fijá el label a un valor **LITERAL** (la red que el proxy SIEMPRE comparte, p.ej. `coolify`),
     NO `${VAR:-}` — la interpolación NO ocurre sobre este label, y ni un default `${VAR:-coolify}` dispara; solo el literal cura.
  4. **Redeploy** del recurso (recrea el contenedor con el label corregido).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO uses **"Restart Proxy"** como fix — solo
  re-elige al azar una IP alcanzable y **deja la bomba armada** para el próximo reload. NO confíes en el
  `healthy` del PaaS (no testea end-to-end a través del proxy). NO asumas que `${VAR:-}` se interpola en labels.
- **PREVENCIÓN:** (a) **check sintético EXTERNO end-to-end** (GET público esperando 200/303) — cierra el
  punto ciego del healthcheck; OJO: NO como cron de Actions si el repo no lo tiene en la rama default →
  [GAP-002](GAP-002.md); (b) **guarda de CI** que FALLA si `traefik.docker.network` usa `${...}` —
  aplicada en el repo origen (`compose-guard.yml`), patrón portable a cualquier repo del mismo esquema;
  (c) invariante: el contenedor que el proxy expone debe estar SIEMPRE en una red a la que el proxy esté
  conectado; (d) **[HECHO 2026-07-01]** auditados los ~21 repos (read-only): el label vive SOLO en 3 —
  el repo origen ya literal en `dev` (su rama de deploy); los otros 2 aún `${...}` en `main` → promover
  el literal donde el PaaS trackee esa rama.
- **validated_on:** `dev` · 2026-07-01 · `6660073` (fix verificado EN VIVO: GET público → 200, antes 000)
- **stale_si:** >90 días, o si se cambia el reverse-proxy / esquema de red del PaaS
- **origen:** Lucky-Auth-Plane — postmortem `docs/incidents/2026-07-01-portal-traefik-docker-network.md`   ·   **usos:** 2
- **REFS:** deploy-build-once-promote (esquema PaaS+compose) · [GAP-002](GAP-002.md)   ·   **NEXT:** promover el literal a los 2 repos restantes + canary en scheduler externo
- **estado:** LIVE   <!-- promovida por MLL (endosó el postmortem en sesión) -->

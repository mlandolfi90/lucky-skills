## [DRIFT-002] Tras un redeploy, loguear al portal da "csrf token invalid" y el reload NO recupera

- **TIPO:** DRIFT (token/estado de form vencido tras redeploy)
- **SÍNTOMA (lo observable, NO la causa):** Después de un redeploy (o con una pestaña vieja
  abierta), al loguear en un portal/form aparece `{"detail":"csrf token invalid"}` (HTTP 403);
  el **hard-reload NO recupera** — solo abrir una **PESTAÑA NUEVA** funciona.
- **CAUSA-RAÍZ (1 línea):** el token CSRF del form vive corto (ej. ~15 min) y el redeploy
  recreó el contenedor → token viejo; el reload RE-POSTea el form viejo (CSRF vencido), mientras
  una pestaña nueva hace un GET limpio que emite cookie+token frescos.
- **ACCIÓN (pasos, máx 7):**
  1. Aplicá **Post/Redirect/Get**: ante CSRF inválido en un FORM → **303 (See Other)** a
     `GET /login?expired=1` (emite cookie+token nuevos; el reload re-GETea limpio, sin re-POST).
  2. Mostrá "tu sesión de login expiró" en ese GET.
  3. Mantené el **403 JSON** para clientes API (no-form).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** no devuelvas un **403 JSON a un FORM
  de navegador** (dead-end para el humano, asimétrico con el path de password-incorrecto que sí
  re-renderiza); no uses **302** — el status correcto del PRG es **303 (See Other)**.
- **PREVENCIÓN (cómo evitar reincidencia):** todo form con CSRF de vida corta + redeploys
  necesita recuperación graceful (PRG); cubrilo con un test (form POST CSRF malo → 303 a
  `/login?expired=1`; JSON POST CSRF malo → sigue 403).
- **validated_on:** `dev` · 2026-06-26 · `<sha>`
- **stale_si:** >90 días, o si el portal cambia el manejo de CSRF/sesión
- **origen:** Lucky-Auth-Plane RUN-LEDGER (portal CSRF login vencido → PRG)   ·   **usos:** 1
- **REFS:** patrón Post/Redirect/Get   ·   **NEXT:** si reaparece en otro portal/login → cross-repo, candidato a checklist
- **estado:** LIVE   <!-- promovida por MLL (endosó el aprendizaje en sesión) -->

## [GREP-002] El endpoint "documentado" da 404 en el servicio deployado — la ruta real difiere de la doc/memoria (litellm cost map)

- **TIPO:** GREP (re-derivación: la doc/el recuerdo no es la verdad del deployado)
- **SÍNTOMA (lo observable, NO la causa):** llamás un endpoint sacado de la doc upstream o de
  memoria (ej. litellm `GET /get/litellm_model_cost_map`) y el servicio deployado responde 404,
  aunque el servicio está sano y la feature existe.
- **CAUSA-RAÍZ (1 línea):** la ruta real depende de la VERSIÓN deployada (en el litellm del stack
  es `GET /public/litellm_model_cost_map`, público y sin auth) — la doc/memoria describe otra
  versión.
- **ACCIÓN (pasos, máx 7):**
  1. No insistas con la ruta de la doc: preguntale al deployado (su `/openapi.json`, `/docs`, o
     grep del código de la versión exacta que corre).
  2. Para el cost map de litellm del stack: `GET /public/litellm_model_cost_map` (2997 entradas,
     sin Bearer).
  3. Asentá la ruta verificada en el código con el porqué (evita el re-descubrimiento).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO asumir que el 404 significa "la
  feature no existe" ni "hace falta auth"; NO probar Bearers/headers al azar contra la ruta
  equivocada.
- **PREVENCIÓN (cómo evitar reincidencia):** ante 404 de un endpoint "conocido", el primer paso
  es SIEMPRE el contrato del deployado (openapi/código de esa versión), no la doc general.
- **validated_on:** `dev` · 2026-07-03 · `/public/...` respondiendo 200 en producción del stack (usado por `fetch_model_cost_map`, corrida catalogo-ctx-auto PASS)
- **stale_si:** >90 días, o upgrade de litellm que cambie la ruta
- **origen:** Lucky-Auth-Plane (corrida catalogo-ctx-auto: `/get/...` → 404, `/public/...` → 200)   ·   **usos:** 1
- **REFS:** keyring/litellm_admin.py `fetch_model_cost_map`   ·   **NEXT:** —
- **estado:** LIVE

## [DRIFT-006] La metadata del PaaS (sha/tag "deployado") no rota con los deploys — un verificador que la lea declara FAIL sobre un deploy sano

- **TIPO:** DRIFT / FALSO-ROJO (metadata del panel ↔ realidad del contenedor)
- **SÍNTOMA (lo observable, NO la causa):** el deploy-verifier (o vos) lee del panel/API del PaaS
  el `git_commit_sha` / tag de la app y NO coincide con el commit recién deployado → veredicto
  FAIL "deploy infiel"… pero la app en vivo YA sirve el comportamiento nuevo.
- **CAUSA-RAÍZ (1 línea):** en Coolify (app pull-based por imagen) esos campos quedan CONGELADOS
  con el valor del setup inicial — no son evidencia del contenedor corriendo.
- **ACCIÓN (pasos, máx 7):**
  1. Ignorá la metadata del panel como evidencia dispositiva.
  2. Provenance FUNCIONAL: endpoint de versión de la app (`/api/version` con sha horneado en la
     imagen) o marcadores del cambio en la respuesta viva (HTML/JSON) + `git log -S` del marcador.
  3. Si el verificador declaró FAIL solo por metadata: refutalo con la provenance funcional y
     dejalo asentado (no re-deployes a ciegas).
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** NO redeployar/reiniciar "para que tome
  el sha" (no cambia la metadata congelada y agrega churn); NO editar la metadata a mano en el
  panel (maquilla, no prueba).
- **PREVENCIÓN (cómo evitar reincidencia):** toda app del stack expone su sha de build en un
  endpoint liviano desde el día 1; los verificadores de deploy DEBEN usar provenance funcional,
  jamás metadata del panel.
- **validated_on:** `dev` · 2026-07-03 · refutación probada en corridas catalogo (deploy-verifier FAIL por `git_commit_sha` congelado vs marcadores vivos + `/api/version`; patrón re-confirmado hoy con sha `fa3127a` vivo y metadata intacta)
- **stale_si:** >90 días, o si Coolify pasa a actualizar `git_commit_sha` en pull-based
- **origen:** Lucky-Auth-Plane RUN-LEDGER (corridas catálogo; app uuid en VPS-B con PORTAL_TAG congelado)   ·   **usos:** 2
- **REFS:** DRIFT-004 (el endpoint de versión sirve para ambos)   ·   **NEXT:** —
- **estado:** LIVE

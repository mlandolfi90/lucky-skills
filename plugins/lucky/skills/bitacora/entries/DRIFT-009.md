## [DRIFT-009] El panel de la extensión muestra la versión NUEVA pero la UI inyectada no cambió → content script viejo

- **TIPO:** DRIFT
- **SÍNTOMA (lo observable, NO la causa):** recargaste la extensión (↻ en `chrome://extensions`), el side panel / popup muestra la versión NUEVA, pero la barra/UI inyectada EN LA PÁGINA sigue con el comportamiento o estilo VIEJO — "mi fix no funcionó, sigue igual".
- **CAUSA-RAÍZ (1 línea):** el content script se inyecta al CARGAR la página; recargar la extensión NO re-inyecta en pestañas ya abiertas. El panel (contexto de la extensión) SÍ se refresca al recargar; el content script (la UI en la página) NO, hasta un F5 de la PÁGINA.
- **ACCIÓN (pasos):**
  1. **F5 la PÁGINA** (no solo ↻ la extensión) para re-inyectar el content script.
  2. Poné un **version-stamp visible**: en el panel (lee `chrome.runtime.getManifest().version`) Y un `console.info("content.js vX")` al inyectar. Compará la versión del CONTENT SCRIPT (consola), no la del panel.
- **ANTI-ACCIÓN (camino muerto):** NO shippees más "fixes" creyendo que el anterior falló — antes confirmá que el content script en esa pestaña ES la última versión (consola), no asumas por el panel. Perdimos varias iteraciones por esto.
- **PREVENCIÓN:** bump del `manifest.version` por cada cambio de código + stamp en consola al inyectar → el operador confirma en 5s "última versión" y distingue "fix no anda" de "content viejo".
- **validated_on:** `dev` · 2026-07-10 · `ee3b470`
- **stale_si:** >90 días sin re-validar, O MV cambia el modelo de inyección
- **origen:** postmortem popover-bleed (vault-popover-bleed-2026-07-09); confundió el diagnóstico ~5 versiones · **usos:** 1
- **REFS:** n/a · **NEXT:** cualquier debug de extensión Chrome — chequear versión del content script primero
- **estado:** CANDIDATE

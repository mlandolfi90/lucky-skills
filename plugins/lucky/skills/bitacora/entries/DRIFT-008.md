## [DRIFT-008] "Mi fix no anda": recargaste la extensión (↻) pero la UI inyectada sigue con el comportamiento viejo

- **TIPO:** DRIFT
- **SÍNTOMA (lo observable, NO la causa):** Shippeás un fix a una extensión de navegador, recargás la extensión (botón ↻ en chrome://extensions), el panel/popup YA muestra la versión nueva — pero la barra/popover/overlay inyectado en la página se comporta como ANTES. Concluís (mal) que el fix no funcionó y seguís "arreglando".
- **CAUSA-RAÍZ (1 línea):** Recargar la extensión refresca el panel/background, pero el **content script solo se refresca al recargar la PÁGINA (F5)** — la pestaña ya abierta seguía corriendo el `content.js` viejo (la recarga de extensión NO re-inyecta en pestañas abiertas).
- **ACCIÓN (pasos):**
  1. Tras cada recarga de extensión: **F5 en la página objetivo** antes de evaluar el fix.
  2. Version-stamp visible en AMBAS superficies: el panel muestra su versión (`chrome.runtime.getManifest().version`) Y el content script loguea la suya en consola (`console.info("content.js vX.Y.Z")`) al inyectarse.
  3. Ante "el fix no anda": primero comparar versiones panel↔consola; si difieren, no hay bug nuevo — hay script viejo.
- **ANTI-ACCIÓN (el camino muerto):** Iterar "fixes" sobre un fix que nunca llegó a ejecutarse — en el caso real varios "no funcionó" eran content script viejo, sumando versiones fantasma al debug.
- **PREVENCIÓN:** Bump de `manifest.version` por cada cambio de código + el version-stamp doble como parte del esqueleto de toda extensión Lucky desde el día 1 — el operador confirma en 5s y distingue estructuralmente "fix roto" de "código viejo".
- **validated_on:** `dev` · 2026-07-09 · extensión Lucky-Debugger (varios falsos "no funcionó" atribuidos en el postmortem)
- **stale_si:** >90 días sin re-validar, O el manifest pasa a un modelo de inyección sin content scripts persistentes
- **origen:** postmortem popover-bleed 2026-07-09 (cosecha por INTENSIDAD) · **usos:** 1
- **REFS:** hermana conceptual: [DRIFT-004](DRIFT-004.md) (pestaña vieja contra server nuevo — misma clase "cliente viejo parece bug nuevo") · **NEXT:** n/a
- **estado:** LIVE

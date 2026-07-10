## [DRIFT-008] UI de content-script (light DOM) se ve inflada/rota y sus PROPIOS box-props están en 0 → el CSS de la página se filtra a un HIJO

- **TIPO:** DRIFT
- **SÍNTOMA (lo observable, NO la causa):** un elemento de la UI inyectada (barra/popover/overlay) se ve más alto/roto de lo esperado. Al medir con `getComputedStyle` sus PROPIOS `margin`/`padding`/`min-height` están en `0`, pero su `getBoundingClientRect().height` es grande. (Ej: un `<label>` flex de 42px con todos sus box-props en 0 → adentro un `<input>` checkbox de 42px; el texto es 13px.)
- **CAUSA-RAÍZ (1 línea):** la UI inyectada vive en el LIGHT DOM y hereda/matchea el CSS de formularios de la página (`input{min-height}`, `label{margin}`) — que infla un HIJO, no el contenedor que estás reseteando.
- **ACCIÓN (pasos):**
  1. **INSTRUMENTÁ, no adivines:** logueá `getComputedStyle` + `getBoundingClientRect` del sospechoso Y de sus hijos.
  2. Band-aid: `!important` en el elemento EXACTO que se infla (a veces el `<input>` hijo, no el label). Reset por-propiedad.
  3. **Permanente: Shadow DOM** — meté toda la UI inyectada en un `attachShadow({mode:'open'})` → la página no puede filtrarse (mata la clase entera). Gotcha: `:root`→`:host` para los tokens; el host va al `body`, no al shadow.
- **ANTI-ACCIÓN (camino muerto):** NO sigas reseteando el CONTENEDOR si sus box-props ya son 0 (el gordo es un hijo); NO adivines regla por regla (quemó ~10 versiones). Un preview que NORMALIZA los defaults del navegador (le pone `margin:0` al checkbox que el real no tiene) MIENTE.
- **PREVENCIÓN:** UI inyectada en sitios arbitrarios → Shadow DOM de arranque. Predicado de propiedad puro (`isLuckyElement`).
- **validated_on:** `dev` · 2026-07-10 · `ee3b470`
- **stale_si:** >90 días sin re-validar, O la barra migra a otro modelo de aislamiento
- **origen:** postmortem completo (vault-popover-bleed-2026-07-09) · RUN CE-A45 Shadow DOM · **usos:** 1
- **REFS:** familia de [[GAP-006]] (light-DOM injected UI; ese es de EVENTOS, éste de CSS) · **NEXT:** si aparece en otra UI Lucky → Shadow DOM
- **estado:** CANDIDATE

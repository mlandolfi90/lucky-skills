## [FALSO-VERDE-001] El accept de una herramienta de variantes en vivo (Live Mode) deja la UI "bien" pero borró funcionalidad del componente

- **TIPO:** FALSO-VERDE
- **SÍNTOMA (lo observable, NO la causa):** tras aceptar una variante visual (impeccable Live
  Mode u homólogo), la página se ve correcta y compila, pero en el diff del fuente faltan
  ramas del componente original (botones condicionales, portals, handlers) que la variante
  no incluía.
- **CAUSA-RAÍZ (1 línea):** el accept promueve AL FUENTE exactamente el JSX que el agente
  escribió como variante; si el agente la recortó "para la demo", el recorte se vuelve
  permanente — regresión silenciosa que ningún build detecta.
- **ACCIÓN (pasos, máx 7, copy-paste si aplica):**
  1. Al generar variantes: copiar el componente COMPLETO en cada una (todas las ramas
     condicionales, portals, aria, handlers); variar solo lo que pide la acción.
  2. Tras el accept: `git diff` del archivo promovido CONTRA el componente original y
     verificar que solo cambió lo intencional; restaurar lo que falte.
  3. Correr typecheck + smoke funcional (no alcanza lo visual).
- **ANTI-ACCIÓN (el camino muerto):** confiar en que "se ve igual y compila"; escribir
  variantes minimalistas para ahorrar tokens.
- **PREVENCIÓN (cómo evitar reincidencia):** regla en la ley de diseño (Lucky-Estilo
  `DESIGN.md` §3: "variante = componente completo") + diff post-accept obligatorio.
- **validated_on:** `main` · 2026-07-03 · `cddf3378` (Lucky-TDU: casi se pierden el botón
  limpiar-búsqueda y el portal del FiltroPanel; restaurados y verificados por verificador fresco)
- **stale_si:** >90 días sin re-validar, O la herramienta agrega preservación funcional propia
- **origen:** RUN-LEDGER Lucky-TDU main 2026-07-03 (RETRO)   ·   **usos:** 1
- **REFS:** Lucky-Estilo/DESIGN.md §3 · Impeccable-Estudio/FASE-B-INFORME.md   ·   **NEXT:** n/a
- **estado:** LIVE

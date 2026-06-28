## [GREP-001] Voy a grep ciego buscando dónde vive un flujo en vez de mirar el mapa

- **TIPO:** GREP
- **SÍNTOMA (lo observable, NO la causa):** El agente arranca un grep/glob ciego
  para encontrar un flujo (cifrado, parseo, gate…), o pregunta "¿dónde está X?",
  sin consultar primero el mapa de Key Files del repo.
- **CAUSA-RAÍZ (1 línea):** Conocimiento de topología no pre-cargado; se re-deriva
  cada sesión (context rot).
- **ACCIÓN (pasos, máx 7):**
  1. PARÁ de grepear. Corré la brújula y leé el último ADR + Key Files del repo.
  2. Anclate al punto de entrada conocido antes de explorar a ciegas.
  3. Si falta el dato: escalá ripgrep → ast-grep → LSP. Nunca empieces por
     búsqueda semántica. Budget de búsqueda acotado (no leas el repo entero).
- **ANTI-ACCIÓN (evita re-derivar):** No leas todo el repo al inicio; no greps a
  ciegas más de unos minutos sin abrir el mapa. La brújula ya ancla branch+ADR+
  estado: usala antes de explorar.
- **PREVENCIÓN:** este patrón ya está mapeado; leé esta entrada (vía la 5ta fuente
  de la brújula), no re-grepees. Si el repo no tiene mapa de Key Files → es un GAP
  de navegación, candidato a un `MAPA.md` corto del repo.
- **validated_on:** `claude/arduous-task-j7zc8p` · 2026-06-28 · `<sha>`
- **stale_si:** >90 días, o si el flujo se refactoriza
- **origen:** blueprint Vademécum (concejo) + lección "anclarse al código real, no al resumen"   ·   **usos:** 1
- **REFS:** `brujula/SKILL.md` (fuentes)   ·   **NEXT:** si el cambio toca un contrato → invocar `crisol`
- **estado:** CANDIDATE   <!-- semilla destilada por el agente; el humano la promueve a LIVE -->

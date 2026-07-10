## [GREP-004] Debug visual/CSS "a ciegas": shippear un fix por propiedad, pedir que testeen, fallar, repetir

- **TIPO:** GREP
- **SÍNTOMA (lo observable, NO la causa):** Un bug visual (espaciado, tamaño, alineación) lleva ya 2+ intentos de fix, cada uno tocando UNA propiedad CSS plausible (gap → margin → reset → `!important`), cada round-trip con "probá ahora" al humano — y ninguno pega. El ciclo se siente productivo pero es adivinanza serial.
- **CAUSA-RAÍZ (1 línea):** Se está mutando sin haber MEDIDO: sin `getComputedStyle` + `getBoundingClientRect` del elemento real en el entorno real, cada fix es una hipótesis a ciegas sobre cuál caja y cuál regla causan el layout.
- **ACCIÓN (pasos):**
  1. Al SEGUNDO fix visual fallido, frená los parches: instrumentá.
  2. ~10 líneas que logueen `getComputedStyle` (margin/padding/min-height/line-height/box-sizing) + `getBoundingClientRect` de los elementos sospechosos **y sus hijos**, en el entorno real.
  3. Leé el log: la discrepancia entre "lo que el CSS dice" y "lo que la caja mide" señala al culpable en UN round-trip. Recién ahí, el fix.
- **ANTI-ACCIÓN (el camino muerto):** Seguir shippeando "fixes" propiedad por propiedad y pedir que testeen — en el caso real quemó ~5 versiones y horas; el diagnóstico instrumentado encontró la causa en un solo tiro.
- **PREVENCIÓN:** Regla de dos strikes: dos fixes visuales fallidos ⇒ obligatorio instrumentar antes del tercero. El costo del log (10 líneas) es siempre menor que el tercer adivinazo.
- **validated_on:** `dev` · 2026-07-09 · extensión Lucky-Debugger v0.9.10/11 (el log reveló al hijo inflado en un tiro)
- **stale_si:** >90 días sin re-validar
- **origen:** postmortem popover-bleed 2026-07-09 (cosecha por INTENSIDAD) · **usos:** 1
- **REFS:** [GAP-007](GAP-007.md) (qué medir: también a los hijos) · **NEXT:** n/a
- **estado:** LIVE

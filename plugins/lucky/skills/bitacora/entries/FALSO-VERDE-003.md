## [FALSO-VERDE-003] El preview/harness de UI muestra la medida "correcta" pero el elemento real difiere — el preview miente

- **TIPO:** FALSO-VERDE
- **SÍNTOMA (lo observable, NO la causa):** Armaste un preview/harness aislado para medir o reproducir un bug de UI; el preview da un valor (ej. pitch 16px) que no coincide con el real en producción (22px). Las decisiones tomadas sobre el preview no se sostienen en el entorno real.
- **CAUSA-RAÍZ (1 línea):** El preview NORMALIZÓ defaults que el entorno real sí aplica — en el caso real le puso `margin:0` al checkbox (que el CSS real no tenía), limpiando el margin del user-agent que era parte del bug.
- **ACCIÓN (pasos):**
  1. Un preview de UI debe **REPRODUCIR los defaults del entorno**, jamás limpiarlos: nada de resets "para que se vea prolijo" que el código real no tiene.
  2. Si el bug involucra CSS de una página anfitriona (UI inyectada), el preview replica también ese bleed (las reglas de la página que matchean tus elementos).
  3. Validación cruzada obligatoria: una medición del preview solo cuenta si coincide con la misma medición en el entorno real.
- **ANTI-ACCIÓN (el camino muerto):** Confiar en el preview porque "es el mismo markup" — el markup era el mismo, el ENTORNO no; el preview limpio dio un diagnóstico falso que sostuvo otro round de fixes errados.
- **PREVENCIÓN:** Todo harness visual lleva un comentario "defaults NO normalizados a propósito"; cualquier reset agregado al harness es un red flag de revisión.
- **validated_on:** `dev` · 2026-07-09 · extensión Lucky-Debugger (preview 16px vs real 22px, detectado en el postmortem)
- **stale_si:** >90 días sin re-validar
- **origen:** postmortem popover-bleed 2026-07-09 (cosecha por INTENSIDAD) · **usos:** 1
- **REFS:** familia light-DOM: [GAP-006](GAP-006.md), [GAP-007](GAP-007.md) · **NEXT:** n/a
- **estado:** LIVE

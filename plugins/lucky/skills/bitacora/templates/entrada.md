# Plantilla de entrada de Bitácora

> Una entrada = un síntoma = una acción. El título ES el síntoma observable, con
> tag `[TIPO-NNN]` para Ctrl-F. TIPO ∈ {GAP, GREP, DRIFT, FALSO-VERDE}. Máx ~20-35
> líneas. Sin secretos (nombres de variable, nunca valores; rutas relativas).
> Copiá el bloque, completá, guardá como `entries/<TIPO-NNN>.md`.

```markdown
## [TIPO-NNN] <síntoma observable, en primera persona del que se atasca>

- **TIPO:** GAP | GREP | DRIFT | FALSO-VERDE
- **SÍNTOMA (lo observable, NO la causa):** <qué ves literalmente; lo que un agente
  podría matchear contra esto>
- **CAUSA-RAÍZ (1 línea):** <por qué pasa>
- **ACCIÓN (pasos, máx 7, copy-paste si aplica):**
  1. <paso>
  2. <paso>
- **ANTI-ACCIÓN (el camino muerto — evita re-derivar):** <qué NO hacer>
- **PREVENCIÓN (cómo evitar reincidencia):** <test/regla/hábito>
- **validated_on:** `<branch>` · <YYYY-MM-DD> · `<sha>`   <!-- OBLIGATORIO. Sin esto nace STALE -->
- **stale_si:** >90 días sin re-validar, O <condición específica del patrón>
- **origen:** <RUN-LEDGER branch fecha | ADR NNNN | patrón XYZ>   ·   **usos:** <n>
- **REFS:** <ADR NNNN | invariante | n/a>   ·   **NEXT:** <si toca X → abrir Crisol/ADR>
- **estado:** CANDIDATE | LIVE | STALE | SUPERSEDED-BY:<id> | RETIRED
  <!-- el agente destila CANDIDATE; el humano promueve a LIVE -->
```

## Campos load-bearing (los lee `scripts/bitacora-stale.sh`)

- `validated_on:` debe contener una fecha `YYYY-MM-DD`. Su ausencia → STALE.
- `estado:` el validador respeta `RETIRED`/`SUPERSEDED-BY` (no los marca STALE).

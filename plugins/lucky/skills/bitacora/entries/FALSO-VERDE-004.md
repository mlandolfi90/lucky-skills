## [FALSO-VERDE-004] Un gate/lint corrido con pipe dentro de una cadena `&&` sale "verde" — pero el FAIL real pasó de largo

- **TIPO:** FALSO-VERDE
- **SÍNTOMA (lo observable, NO la causa):** Un paso de verificación encadenado (`lint | tail -5 && siguiente-paso`) reporta éxito y el flujo continúa (push, promoción, forja) — pero después descubrís que el lint/gate HABÍA fallado: su mensaje de error incluso estaba en pantalla, truncado por el `tail`.
- **CAUSA-RAÍZ (1 línea):** El exit status de un pipeline es el del ÚLTIMO comando: `gate | tail` devuelve el exit de `tail` (0), enmascarando el exit≠0 del gate; el `&&` evalúa ese 0 y sigue.
- **ACCIÓN (pasos):**
  1. Todo gate/lint/verificador corre **SIN pipe** en la posición que decide: capturá la salida primero (`OUT="$(gate ...)"`) y chequeá `$?` desnudo.
  2. Recién después formateá/truncá la salida capturada (`printf '%s' "$OUT" | tail ...`).
  3. Alternativa cuando el pipe es inevitable: `set -o pipefail` en el script — pero la captura explícita es el patrón canónico (es lo que hace la forja).
- **ANTI-ACCIÓN (el camino muerto):** "El paso salió verde, sigo" — en el caso real el lint gritó una incoherencia del catálogo y el push salió igual, dejando una ventana de catálogo-que-miente en main. La MISMA trampa mordió otra vez el mismo día dentro de los greps de una suite de tests.
- **PREVENCIÓN:** En revisión, todo `| tail`/`| head`/`| grep` pegado a un comando que decide un `&&` o un verde es un red flag automático.
- **validated_on:** `dev` · 2026-07-09 · lucky-skills (2 mordidas el mismo día: lint del catálogo enmascarado + greps de test-maquina-scan; antídoto de captura aplicado en la forja y en las suites)
- **stale_si:** >90 días sin re-validar
- **origen:** promoción desde SENALES (señal registrada y confirmada por segunda mordida intra-sesión) · **usos:** 2
- **REFS:** n/a · **NEXT:** candidata a check automático del leak-scan/forja si muerde una tercera vez
- **estado:** LIVE

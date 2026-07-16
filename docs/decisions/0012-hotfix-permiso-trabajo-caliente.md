# 0012 — Hotfix: permiso de trabajo en caliente (iterar con el operador en frente)

- estado: aceptado
- fecha: 2026-07-10
- decide: MLL (operador) — pedido "un mecanismo para iterar rapido conmigo en
  frente"; plan perfeccionado por enjambre adversarial (30 hallazgos, 24
  incorporados) y aprobado
- tags de la familia al sellar: v1.35.0
- relacionado: skill hotfix; Crisol (mecánica ACTIVE + runState); ADR 0010
  enmienda 3 (cosecha por intensidad); bitácora GAP-007/008, GREP-004,
  DRIFT-008, FALSO-VERDE-003/004 (las lecciones que el ciclo absorbe)

## Contexto

Iterar un fix EN VIVO (el operador probando cada versión) no tenía carril:
o se pagaba una corrida Crisol completa por intento — carísimo cuando el
intento NO es la solución — o se trabajaba fuera de la ley. El caso
fundacional (popover-bleed, 2026-07-09) hizo lo segundo: ~10 versiones y
horas sin ledger, y la sesión tuvo que improvisar un "vault" a mano para no
perder la solución en el rollback. El costo de reponer esa improvisación
bajo presión ES el argumento del carril.

Descubrimiento que lo hizo barato: la ley YA banca el ciclo. Con una entrada
ACTIVE en `runState: wip`, el gate permite ediciones y WIP-commits sin
matriz; la matriz completa+verde se exige solo en el commit `runState:
closing`. No hubo que tocar gate ni enforcer.

## Decisión

Nace la skill **hotfix** (v1, prosa pura): el **permiso de trabajo en
caliente** — declarado, acotado, con vigía y con cierre.

1. **UN permiso para todo el hotfix:** entrada ACTIVE completa
   (Tier/Fecha/TARGET/MODEL + `BASE: <sha>` + bloque VEREDICTOS con
   `runState: wip` desde el día 0). Solo mesa caliente (`pc-local`,
   `docker-local`, `paas:…@dev`) — jamás @testing/@production.
2. **Betas versionadas con su resultado guardado** (requisito literal del
   operador): vault en el repo (`docs/refactor/_hotfix/<slug>-<fecha>/`)
   con `INTENTOS.md` — una fila por beta (versión · commit · hipótesis ·
   cambio · veredicto ✓/~/✗ con cita textual · evidencia), WIP-commit por
   CADA bump para que cada fila apunte al código exacto. El árbol se
   revierte a BASE entre hipótesis (nunca acumula hacks; los veredictos no
   se contaminan). Vault bajo ZERO_LEAK (scrub al transcribir; el leak-scan
   de toda forja futura lo barre).
3. **La disciplina anti-adivinanza** viene de la bitácora, no de teoría:
   2 strikes ⇒ instrumentar (GREP-004), stamp confirmado o no hay veredicto
   (DRIFT-008), releer diff tras replace_all (GAP-008), previews con
   validación cruzada (FALSO-VERDE-003).
4. **Formalización = UNA corrida:** al hallar la solución, árbol a
   BASE+solución (`git restore --source` + diff de la solución,
   forward-only), re-clasificación del Tier sobre ESE diff, matriz completa
   y cierre. Sin solución: cierre honesto, vault preservado.
5. **Exención del techo:** los ciclos beta con operador presente NO cuentan
   para el techo de 3 iteraciones del Crisol — ese techo gobierna loops
   Plan↔FAIL autónomos; en el hotfix el circuit-breaker es 2-strikes + el
   humano decide cada ciclo. `Iteraciones: n/3` del cierre cuenta solo la
   fase de formalización. (Sin esta exención el carril legalizaría ~10
   betas con una mano y las criminalizaría con la otra.)
6. **El vault es postmortem-ready:** con ≥3 filas o cierre sin solución se
   ofrece la cosecha por INTENSIDAD (ADR 0010 enmienda 3) con el vault como
   material; la marca `cosechado: <fecha> → <IDs>` en el header evita la
   cosecha duplicada entre sesiones (ya ocurrió el 2026-07-10).

## Lo que NO es

- **No suspende la ley:** usa ACTIVE+wip que ya existía; el gate y el
  enforcer no se tocaron.
- **No es un bypass de tier:** el cierre re-clasifica con el checklist §1
  sobre el diff real de la solución.
- **No corre solo:** sin operador presente no hay veredictos y no hay ciclo
  — ese caso es una corrida Crisol normal.

## Consecuencias

- (+) El costo por intento fallido baja de "una corrida" a "una fila de
  tabla + un WIP-commit".
- (+) Cada beta queda consultable para siempre (`git show <commit>` desde
  la fila) — el requisito "versionados con su resultado guardado".
- (+) El dolor queda destilable sin trabajo extra (vault = postmortem).
- (−) WIP-commits por bump ensucian la historia de dev — aceptado: es el
  respaldo, y el cierre entrega el diff limpio.
- (=) Endoso humano intacto en cada eslabón: veredicto por beta, decisión
  de seguir/parar, endoso de cosecha.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.3.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

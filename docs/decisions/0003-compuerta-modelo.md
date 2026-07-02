# 0003 — Compuerta de Modelo: el Paso 0 fija el modelo de los sub-agentes, fail-closed

- estado: aceptado
- fecha: 2026-06-21
- decide: MLL (operador) vía Steward del Crisol
- tags de la familia al sellar: ~v1.13.0 (Crisol con Compuerta de Modelo en el Paso 0)
- relacionado: ADR 0002 (gate de cobertura fail-closed, cuyo `_coverage_state` enforza esta regla por construcción); SKILL.md §4 Paso 0 · §3 puntos 1 y 6 · §5 catálogo; `templates/run-ledger.md` (campo `- MODEL:`)

## Contexto

El Paso 0 del Crisol ya fija el **`TARGET:`** de la corrida fail-closed: dónde corren y
se verifican los tests, confirmado con el humano en una pregunta de 1 tecla, y sin
respuesta → FRENA (jamás asume local). Faltaba la decisión simétrica sobre **QUÉ modelo**
corren los sub-agentes de la corrida. Hasta hoy eso quedaba implícito en el mapeo de
tiers por complejidad (§3), sin un gate explícito ni registro en el ledger: el líder
podía spawnear con cualquier modelo sin que el humano lo eligiera ni quedara constancia.

El operador pidió una **Compuerta de Modelo** en el Paso 0 con el mismo rigor que el
TARGET: el humano elige el modelo de los agentes de la corrida ANTES de spawnear; sin
respuesta, FRENA. Y que el enforcement reuse la maquinaria existente (la matriz de
veredictos + el gate de cobertura de v1.12.0), SIN tocar hooks ni tests.

## Decisión

Se agrega la **Compuerta de Modelo** al Paso 0 (§4), fail-closed, junto al TARGET:

1. **Enumeración en runtime (Ley viva, no hardcode).** El líder **enumera del ENTORNO**
   los alias que la tool de spawn realmente acepta (hoy `opus`/`sonnet`/`haiku`/`fable`)
   más la opción `default`, y se los presenta al humano. La lista NO se hardcodea: sale
   un modelo nuevo, aparece solo. Se enumera **del entorno, NO de memoria**; si el líder
   no puede enumerar, fail-closed: pregunta con lo que tenga y **jamás inventa un alias**.

2. **Constraint alias-no-versión.** La tool acepta **alias de familia, no versiones
   puntuales**: `opus` resuelve a la versión vigente; no se puede pinear "4.8 vs 4.7".
   Se documenta para que nadie espere granularidad de versión que la tool no ofrece.

3. **Uniforme vs default.** El humano elige un **alias → uniforme** (ese modelo para
   TODOS los agentes de la corrida) o **`default` → por-rol por complejidad** (el mapeo
   de tiers de §3: mecánica → económico · juicio → alto · síntesis → frontera).
   **Sin respuesta → FRENA** (no spawnea; sin humano → ABORTAR), igual que el TARGET.

4. **Gobierna sub-agentes, no al líder.** La compuerta fija el modelo de los SUB-agentes;
   el líder ya corre en el modelo de la sesión y no se toca.

5. **Registro.** El modelo confirmado se anota como **`MODEL:`** en la entrada del ledger
   (igual que `TARGET:`), con valores `<alias> (uniforme)` | `default (por-rol)`.

### Reconciliación de §3 (puntos 1 y 6)

El contrato de selección de modelo cambió (caso legal c de §2: cambia el contrato → tier
completo + ADR), así que se editan AMBOS puntos que lo mencionaban, para no dejar la ley
contradictoria: el **punto 1** y el **punto 6** ahora referencian la Compuerta del Paso 0
y **condicionan la declaración por-rol a `MODEL: default`** (con un alias pin uniforme no
hay tiers por-rol que declarar). Es la misma edición de contrato, no scope creep.

### Enforcement: reusar el gate de cobertura de v1.12.0 (sin tocar hooks)

Se agrega la regla **`MODEL`** al catálogo de la matriz (§5), trigger **"siempre"**,
clase **M (mecánica)**, veredicto emitido por **`gate`** (igual que `TARGET`/`REGLA0`).
No se inventa un `model-verifier`: es chequeo de **presencia**, no de juicio.

El enforcement cae **por construcción**: el `_coverage_state` del `crisol_gate.py`
(ADR 0002) es **rule-agnóstico** — exige que toda celda `[V]` de la matriz sea
`PASS`/`N-A` con `runState: closing`, sin hardcodear IDs. Agregar `MODEL` como regla de
trigger "siempre" hace que una corrida no pueda cerrar sin su veredicto **sin tocar una
sola línea** de `crisol_gate.py`, `crisol-enforcer.sh` ni `tests/test-enforcer.sh`.
Tocar esos `.py`/`.sh` sería scope creep.

## Frontera conocida (idea parqueada)

El gate enforza la **DECLARACIÓN** de MODEL al cierre ("cerró sin MODEL"), **NO** que los
agentes hayan **CORRIDO** efectivamente en ese modelo. Es la misma paridad honesta que el
TARGET: el gate exige que el TARGET esté declarado, no garantiza que los tests corrieran
físicamente ahí. Enforzar el modelo en spawn-time exigiría un hook sobre la tool de spawn
(interceptar cada Agent y validar su `model` contra el `MODEL:` del ledger), hoy no
disponible. Registrado como deuda de endurecimiento futuro:

> **PARKED:** atar el modelo real de cada sub-agente al `MODEL:` declarado — un hook
> sobre la tool de spawn que valide el `model` de cada Agent contra el ledger en
> spawn-time — para que "declaré `opus` pero spawneé `haiku`" no sea una vía silenciosa
> de divergencia. Hoy no hay hook sobre spawn → parqueado.

## Consecuencias

- **Positivas:** el humano elige el modelo de la corrida explícitamente y queda
  constancia en el ledger; la Compuerta es simétrica con el TARGET (mismo Paso 0, mismo
  fail-closed); el enforcement reusa el gate de cobertura existente sin tocar hooks ni
  tests (cero superficie nueva de bug en los guardianes); la enumeración runtime sigue el
  patrón Ley viva (un modelo nuevo aparece solo, sin editar la skill).
- **A vigilar:** la honestidad del gate es de **declaración**, no de **ejecución** (ver
  Frontera parqueada) — mismo límite consciente que el TARGET; si en el futuro hay hook
  sobre spawn, esa frontera se puede cerrar. La fila `MODEL` es ahora load-bearing en la
  matriz: una corrida que la omita con trigger "siempre" → FAIL del gate de cobertura.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.19.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags`), seguir la del repo e informar al humano.

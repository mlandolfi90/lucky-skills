# 0002 — gate de cobertura: el commit de cierre exige la matriz de veredictos completa y verde (fail-CLOSED acotado)

- estado: aceptado
- fecha: 2026-06-21
- decide: MLL (operador) vía Steward del Crisol
- tags de la familia al sellar: ~v1.12.0 (Crisol endurecido: reglas verificadas-por-agente + gate de cobertura)
- relacionado: RUN-LEDGER `docs/refactor/_crisol/RUN-LEDGER.md` (corrida 2026-06-21); ADR 0001 (loader); el invariante de paridad de guardianes (RETRO v1.11.0)

## Contexto

`crisol_gate.py` es un hook PreToolUse cuya filosofía de diseño (docstring L4-7) es
**fail-OPEN total**: ante cualquier duda, error o excepción → exit 0 (permitir). La
razón es sólida: un hook global que brickea el Claude Code del usuario sería el colmo
de la ironía en un sistema anti-defectos.

Los dos guardianes deterministas (`crisol_gate.py` + `crisol-enforcer.sh`) hasta hoy
validan solo la **FORMA** del ledger ACTIVE (Tier + Fecha + TARGET). El gap real
reportado por el operador: las reglas de **JUICIO** (Open/Closed, atomicidad, costura,
conformidad, varias §2) no tienen guardián automático — dependen de que el líder
spawnee verificadores que **puede saltear**. Un líder apurado cierra una corrida con
reglas sin verificar y nada lo detiene.

La corrida que crea ~v1.12.0 convierte esas reglas en verificaciones-por-agente con
**veredicto binario por regla** (la "matriz de veredictos", machine-checkable, en el
bloque `<!-- VEREDICTOS:BEGIN -->`..`<!-- VEREDICTOS:END -->` de la entrada ACTIVE).
Falta la RED FINAL: un gate que impida **cerrar** sin la matriz completa y verde.

## Decisión

Se agrega al `crisol_gate.py` un **gate de cobertura fail-CLOSED**, como **EXCEPCIÓN
ACOTADA** al principio fail-open global. La excepción se limita estrictamente a:

1. **el commit de cierre** — atado a `runState`, NO a STATUS. El commit que cierra pone
   `runState: closing` en el bloque VEREDICTOS; los WIP-commits ponen (o dejan)
   `runState: wip` y pasan sin exigir matriz. Esto resuelve el "dance ACTIVE→CLOSED" y
   la meta-recursión (§6): la corrida no necesita degradar su propio STATUS para evitar
   auto-bloquearse — itera con `wip` y solo el último commit declara `closing`.
2. **el chequeo de cobertura** — el gate solo mira si la matriz está completa y verde.
   No reemplaza ni duplica a ningún verificador; es la red que exige que los veredictos
   EXISTAN, no quién los emite.

### Gramática TRIVIAL (condición 4 del Steward)

`green ⟺ veredicto ∈ {PASS, N/A}` (case-insensitive). Cualquier otra cosa —`FAIL`,
`PENDIENTE`, vacío, o cualquier string inesperado— **NO es green**. Trivial a propósito:
una gramática rica invita a bugs en el propio guardián (justo lo que un gate anti-defectos
no puede permitirse) y a divergencia entre los dos guardianes (la lección v1.11.0: el
borde de mayúsculas donde el oráculo era ciego). Por eso el case-insensitive es explícito
y probado en el fixture (D5: `fail`/`Fail`; D6: `PASS`/`pass`/`N/A`).

### `ausente=skip → fail-CLOSED` vs `ilegible=bug → fail-OPEN`

La sutileza central de la excepción:

- Una matriz `closing` **vacía-pero-presente** (bloque sin líneas `[V]`, o ausente
  estando `runState: closing`) → **CLOSING_INCOMPLETE → bloquea**. Eso es el agujero que
  el gate cierra: un líder que pone `closing` sin completar la matriz está **salteando**
  la cobertura, y saltear DEBE fallar-cerrado. (fixture D2)
- Un ledger **ilegible** (no se puede leer/parsear, excepción de I/O o de parseo) →
  **WIP → permite**. Eso es un **bug del propio gate o del disco**, no un skip del líder;
  brickear por ahí violaría la filosofía global y dejaría al usuario sin poder commitear
  por un defecto nuestro. fail-OPEN estricto a ese borde.

La distinción es deliberada: el gate distingue "el humano omitió el trabajo" (se castiga)
de "la herramienta no pudo leer" (se perdona). Toda excepción de parseo en
`_coverage_state` devuelve `WIP` (permite); solo `runState: closing` + matriz realmente
incompleta/roja bloquea.

### Diseño: AGREGAR, no reescribir

Se **agrega** `_coverage_state(repo, branch)` (espejo de `_ledger_state`, mismo estilo,
`utf-8-sig errors=replace`) + una rama de 4 líneas en el caso `state == "ACTIVE_OK"` de
la sección commit + el `MENSAJE_COBERTURA`. El corazón estable del gate no se toca
(Open/Closed). Paridad asimétrica justificada: **NO** se toca `crisol-enforcer.sh` — el
enforcer bash no ve commits (solo ediciones de archivo), igual que el piso B es solo del
gate Python; los delimitadores `<!-- ... -->` son comentarios HTML que el `awk` del
enforcer ya ignora.

## Meta-recursión (§6): cumplir la regla, no esquivarla

Esta corrida juzga el diff que la crea (v1.11.0 juzga ~v1.12.0). El gate nuevo entra en
vigor para su propio commit de cierre. La resolución NO es esquivar el gate (poner
`wip` para colarse, o degradar STATUS): es **cumplirlo** — esta corrida pone su propia
`runState: closing` con la matriz de veredictos completa y verde, y así el commit de
cierre pasa **porque satisface la regla**, no porque la evade. El gate se dogfoodea
contra sí mismo en su primer cierre.

## Frontera conocida (idea parqueada)

El gate enforza la **cobertura del cierre**, no la **existencia del cierre**. Un agente
que **nunca** pone `runState: closing` puede dejar una corrida ACTIVE colgada
indefinidamente (commitea todo como `wip` y se va). Eso NO lo atrapa el gate —es
enforcement de **proceso**, no de gate—: la corrida ACTIVE huérfana queda **visible para
la próxima brújula** (que detecta corridas-a-medias y ancla al estado real). Registrado
como deuda de endurecimiento futuro:

> **PARKED:** atar una corrida ACTIVE "colgada" (sin `closing` y sin actividad reciente)
> a una señal de proceso —brújula la marca, o un timeout que la escale a MLL— para que
> "nunca cerrar" no sea una vía silenciosa de evadir la cobertura.

## Consecuencias

- **Positivas:** ningún cierre sin la matriz completa+verde; el JUICIO gana red final
  determinista; la excepción es minúscula y auditable (una función + 4 líneas); el resto
  del gate sigue fail-open intacto.
- **A vigilar:** la matriz es ahora load-bearing (formato tan rígido como `- STATUS:`);
  el fixture (Grupo D, 11 casos) es la fuente única de verdad de qué cuenta como green y
  prueba los bordes (parcial D3, ilegible/vacía D2, mayúsculas D5, N/A D8, WIP-no-rompe
  D7, FO-15 D10, A-muerde-antes D11). Un cambio de formato de la matriz exige tocar el
  parser Y el fixture en el mismo commit (paridad parser↔fixture).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.3.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

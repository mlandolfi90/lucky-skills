# 0008 — ATOMICIDAD: citación por tamaño (las líneas convocan al juez, no sentencian)

- **Estado:** aceptada (corrida Crisol 2026-07-06, Tier Completo)
- **Contexto previo:** `docs/refactor/_crisol/PLAN-atomicidad-gate.md`

## Contexto

`ATOMICIDAD` (=SRP=la S de SOLID) ya se enforza en el Crisol: el `design-verifier`
la dictamina sobre el diff y el gate de cobertura (`crisol_gate.py:_coverage_state`)
bloquea el cierre si falta o está en rojo. Pero el operador llegó con archivos de
3000 líneas en sus repos y la pregunta correcta: *"¿SOLID nace desde la primera
línea?"*. El diagnóstico halló **tres huecos** por donde el código se escapa de esa
cadena:

- **A — opt-in / no-cierra:** el Crisol es de invocación explícita; una corrida
  puede abrir `ACTIVE` y WIP-commitear con `runState: wip` sin que el
  `design-verifier` corra nunca. O el repo nunca adoptó el Crisol.
- **B — rigor:** el juez (LLM) ve el diff pero nada lo obliga a mirar la unidad que
  el diff engordó; puede sellar `ATOMICIDAD PASS` de ojito.
- **C — deuda pre-existente invisible:** el Crisol solo juzga el diff; el código ya
  escrito no se re-mira (`auditoria-solid` existía pero nunca se corría ni se
  señalaba).

Principio rector de la decisión: **las líneas no son el criterio de SRP** (un
archivo largo puede ser legítimo: lookup, switch exhaustivo, generado). Pero el
tamaño ES una señal barata y mecánica. Se usa como **citación al juicio, jamás como
veredicto**.

## Decisión

1. **Cambio 1 (ataca B) — escaneo-citación.** `scripts/atomicidad-scan.sh` (clase M,
   token-free) lista las unidades de código que el diff deja por encima del umbral
   `T`. El `design-verifier` lo corre como pre-paso OBLIGATORIO: cada unidad citada
   es un ítem que su veredicto `ATOMICIDAD` resuelve **por nombre** (larga-legítima
   → N/A · responsabilidad múltiple → FAIL). Reusa `crisol-enforcer.sh
   --print-code-policy` como fuente única de "qué es código" (cero drift, lección
   F1). Enunciado en `crisol/SKILL.md` §2 + `auditor-checklist.md` §B — **sin ID
   nuevo en §5** (endurece la verificación de una regla existente, no agrega regla).
2. **Cambio 2 (ataca C) — señal en la brújula.** Fuente 3: si el repo adoptó
   `arquitectura` y nunca corrió `auditoria-solid` → SEÑAL no-normativa "deuda SOLID
   sin auditar → /arquitectura". Read-only, espejo de "ley atrasada".
3. **Cambio 3 (ataca A) — aviso no-bloqueante en los guardianes.** `crisol_gate.py`
   y `crisol-enforcer.sh` emiten a stderr un aviso `[CRISOL-ATOMICIDAD]` cuando un
   edit toca un archivo de código ≥ `T`. **`exit 0` siempre** (fail-open y
   anti-jidoka intactos: nudge, no gate — el gate no puede juzgar SRP). Paridad
   EXACTA gate↔enforcer (mismo umbral, mensaje byte-idéntico) **probada por
   `tests/test-enforcer.sh` Grupo I** (disciplina F1, cero cisma de guardianes).
4. **Umbral `T` configurable y ajustable por chat.** Precedencia: env
   `CRISOL_ATOMICIDAD_T` → `docs/refactor/_crisol/atomicidad.conf` → 400. El default
   400 es una *señal* de arranque, no una ley. Cuando el operador pide por chat
   "subí el umbral a N", el agente escribe `N` en el `.conf` del repo (versionado,
   auditable). 12-factor: valor por entorno, no horneado.

## Consecuencias

- Un diff que engorda una unidad past `T` ya no puede cerrar con `ATOMICIDAD PASS`
  sin que el juez la haya abordado por nombre (Hueco B cerrado).
- El aviso per-edit nudgea incluso fuera de una corrida (Hueco A mitigado; su otra
  raíz —corridas que no cierran— queda parqueada).
- La deuda pre-existente aflora sola vía la brújula (Hueco C).
- **Fail-open preservado:** ningún camino nuevo bloquea per-edit; el único
  enforcement duro sigue siendo el gate de cobertura al cierre (ya existente).
- **Paridad de guardianes preservada:** el aviso vive en ambos, probado idéntico.

## Alternativas descartadas

- **Bloquear por tamaño:** viola "las líneas no son el criterio" + anti-jidoka +
  fail-open. Descartada: el tamaño cita, el juez sentencia.
- **Umbral horneado:** viola 12-factor; el repo ya castiga taxonomías hardcodeadas.
- **Regla nueva en §5:** `ATOMICIDAD` ya existe; un ID nuevo sería duplicación.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

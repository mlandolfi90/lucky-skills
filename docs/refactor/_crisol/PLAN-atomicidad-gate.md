# PLAN quirúrgico — cerrar el hueco de ATOMICIDAD (SRP) en el Crisol

> **Modo:** PLAN-ONLY. No se tocó la ley. Pedido por MLL: *"¿el Crisol respeta
> SOLID desde la primera línea? me parece que hay cosas que cambiar acá."*
> **Ancla:** v1.27.0. **Estado:** espera decisión de MLL sobre qué bajar.

---

## Diagnóstico (con evidencia en el código real, no teoría)

La cadena de enforcement de `ATOMICIDAD` (=SRP=la S de SOLID) HOY, de punta a punta:

1. **El `design-verifier` (LLM) juzga** `ATOMICIDAD` sobre el diff — `auditor-checklist.md`
   §B ítem `[ATOMICIDAD]` (líneas 32-34) + "sin funciones gigantes, sin archivo
   mezcla-todo" (27). Escribe `[V] ATOMICIDAD · PASS|FAIL` a la matriz.
2. **El gate mecánico exige ese veredicto al cerrar** — `crisol_gate.py:_coverage_state`
   (213-315): con `runState: closing`, si falta el `[V] ATOMICIDAD` o está en rojo →
   `exit 2`, no cierra. Es la RED FINAL.

**Conclusión honesta: dentro de una corrida que CIERRA, SRP sí se enforza desde la
primera línea del diff.** No es que "el Crisol diseñe mal". El problema son **tres
huecos por donde el código se escapa de esa cadena**:

### Hueco A — el Crisol es opt-in, y una corrida puede no cerrar nunca
El gate always-on (`crisol_gate.py`) es **fail-open, mecánico, por-edit**: solo exige
que exista la entrada `ACTIVE` (STATUS+Tier+Fecha+TARGET). **No verifica que un
`design-verifier` haya corrido** hasta el commit de cierre con `runState: closing`.
→ Podés abrir una entrada fast-path y **WIP-commitear código para siempre con
`runState: wip`** (los WIP pasan) sin que nadie juzgue `ATOMICIDAD`. O el repo nunca
adoptó el Crisol. **Ahí nacieron tus archivos de 3000 líneas.** (Idea parqueada
relacionada: 2026-06-21 "endurecer la detección de cierre más allá de runState".)

### Hueco B — rigor: el juez puede sellar sin mirar la unidad que creció
`ATOMICIDAD` es clase **J** (juicio LLM). El `design-verifier` ve el diff y emite
PASS — pero **nada lo obliga a mirar específicamente la unidad que el diff engordó**.
Un archivo que pasa de 700→850 líneas puede quedar sellado PASS de ojito. El checklist
dice "sin archivo mezcla-todo" en prosa; no hay un escaneo que **cite la unidad
riesgosa y fuerce el veredicto sobre ella**.

### Hueco C — la deuda pre-existente es invisible
El Crisol solo juzga el diff de cada corrida. El código YA escrito nunca se re-mira.
`auditoria-solid` (ADR 0007, v1.27.0) cubre esto — pero **está construido y nunca se
corrió**. Nada lo señala.

---

## Los cambios (mínimos, cada uno atacando UN hueco)

### CAMBIO 1 — «líneas como CITACIÓN al juez, jamás como veredicto» (ataca Hueco B) 🎯 núcleo del plan

Un **escaneo mecánico de tamaño** (clase M, token-free) que el `design-verifier`
corre ANTES de emitir su veredicto, y cuyo resultado **obliga** a abordar cada unidad
riesgosa por nombre. Las líneas no sentencian: **convocan al juicio**.

- **Artefacto nuevo:** `plugins/lucky/skills/crisol/scripts/atomicidad-scan.sh`
  (como `bitacora-lint.sh`): sobre el diff staged, lista toda unidad de código que
  (a) supera el umbral `T` líneas, o (b) el diff **engorda** cruzando `T`. Output =
  tabla `archivo · líneas · Δ`. **NO emite veredicto** — solo la lista de citaciones.
  Tests en `tests/test-atomicidad-scan.sh`.
- **Umbral `T` CONFIGURABLE, jamás hardcodeado** (12-factor; env `CRISOL_ATOMICIDAD_T`,
  default sugerido 400 líneas como *señal*, no como ley). Ajustable por repo/lenguaje.
- **Enmienda a `auditor-checklist.md` §B `[ATOMICIDAD]`** (fuente única, +2 líneas):
  "el `design-verifier` corre `atomicidad-scan.sh`; **toda unidad citada es un ítem
  OBLIGATORIO** que su veredicto debe resolver por nombre: *larga-legítima* (tabla de
  lookup, `switch` exhaustivo, generado — UNA responsabilidad) **vs** *responsabilidad
  múltiple* → FAIL con `archivo:línea`. Cruzar `T` **no es FAIL**: es citación."
- **Enmienda a crisol §2 roster** (1 línea): el `design-verifier` corre el escaneo de
  tamaño como pre-paso mecánico de su dictamen de `ATOMICIDAD`.
- **Cero regla nueva en §5** (no infla el catálogo): `ATOMICIDAD` ya existe; esto
  **endurece su verificación**, no agrega un ID. El gate de cobertura no cambia.
- Respeta que "las líneas no son el criterio": el veredicto lo sigue dando el juez
  (larga-legítima vs podrida); el escaneo solo garantiza que **mire**.

### CAMBIO 2 — señal de auditoría pendiente en la brújula (ataca Hueco C) — bajo riesgo

- **Enmienda a `brujula/SKILL.md` fuente 3 (Decisiones)** — espejo exacto del patrón
  "ley atrasada" (no-normativo, solo SEÑAL, read-only): si el repo adoptó
  `arquitectura` pero **nunca corrió `auditoria-solid`** (no hay reporte / marcador) →
  imprimí `deuda SOLID sin auditar → corré /arquitectura (auditoría retroactiva)`.
  La brújula NO audita: solo señala. Sin skill `arquitectura` → omitir.
- **+ correr `auditoria-solid` de verdad** en debugger y demás repos (fuera de esta
  corrida — es uso, no cambio de ley).

### CAMBIO 3 — [DIFERIDO, spike aparte] advisory per-edit en el gate (ataca Hueco A)

Un aviso **no-bloqueante** (`exit 0` + stderr) en el gate cuando un Edit engorda un
archivo de código past `T`, para nudgear incluso FUERA de una corrida.
**NO se baja en esta corrida** — razones:
1. Tocaría los DOS guardianes (`crisol_gate.py` + `crisol-enforcer.sh`), cuya paridad
   EXACTA recién estabilizamos en F1 (v1.26.0). Reabrir esa superficie sin necesidad
   es riesgo puro.
2. Se solapa con la idea parqueada "endurecer cierre más allá de runState" (Hueco A
   tiene otra raíz: corridas que no cierran).
3. El gate es fail-open/mecánico: un advisory per-edit es ruidoso y NO puede juzgar SRP.
→ **Candidato a spike propio** con evidencia, después de que CAMBIO 1 pruebe el umbral
`T` en corridas reales. Se parkea en IDEAS.md, no se bundlea.

---

## Guardas de disciplina (para no violar la propia ley)

- **Evidence-triggered, no especulativo:** la evidencia son los archivos gigantes
  reales de MLL. No inventamos una regla sin dolor (regla del repo: GAP/GREP-001
  retirados por 0 usos).
- **`T` configurable, nunca horneado** (12-factor; el repo ya castiga taxonomías
  hardcodeadas — IDEAS 2026-06-20).
- **N/A para larga-legítima:** el escaneo cita, el juez absuelve lo generado/lookup.
  No se penaliza tamaño per se (respeta tu propia observación).
- **Paridad de guardianes intacta:** CAMBIO 1 vive en el checklist + un script del
  design-verifier, NO en los hooks → cero riesgo sobre la paridad de F1.
- **Fail-open y anti-jidoka preservados:** nada nuevo bloquea per-edit; el único
  enforcement duro sigue siendo el gate de cobertura al cierre (ya existente).

---

## Aterrizaje

- **Tier Completo** (toca `crisol/SKILL.md` + `auditor-checklist.md` + `brujula/SKILL.md`
  — sellados — + script + tests) → **ADR 0008** + forja (con TU autorización) + tag.
- **Verificadores frescos:** `design-verifier` (sobre el propio diff), `scope-verifier`,
  `leak-verifier`, `quality-auditor` (corre `atomicidad-scan` + su suite en el TARGET).
- **§6 la ley se gobierna a sí misma:** v1.27.0 juzga el diff que crea v1.28.0.

## Riesgos

- **Falsos positivos del escaneo** (archivos largos-legítimos citados de más) → mitiga:
  el juez los marca N/A; `T` se calibra con las primeras corridas reales.
- **Umbral demasiado bajo = ruido** → arranca alto (400) y se baja con evidencia.
- **Alcance:** mantener CAMBIO 3 FUERA (el spike aparte) — no dejar que el plan crezca
  a "reescribir los guardianes".

## Decisiones para MLL

1. ¿Bajamos **CAMBIO 1 + 2** juntos en una corrida Tier Completo (recomendado), o solo
   el 1 (el núcleo del arreglo de rigor)?
2. **Umbral `T` inicial:** ¿400 líneas como señal de arranque, u otro número? (es
   ajustable después; solo dispara la mirada del juez, no un FAIL).
3. ¿Autorizás la **forja v1.28.0** al cierre, o cerramos sin forja como hicimos con
   `diseno`?
4. CAMBIO 3 (advisory per-edit) → ¿lo parkeo como spike, o lo querés en el alcance
   pese al riesgo sobre la paridad de guardianes?

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · PLAN (no ley, no ADR).
Ancla: v1.27.0.**

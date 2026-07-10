# 0004 — Invariante "entorno real == `@env` declarado": el TARGET fija el env y el Crisol lo verifica

- estado: aceptado
- fecha: 2026-06-27
- decide: MLL (operador) vía Steward del Crisol
- tags de la familia al sellar: ~v1.14.0 (Crisol con invariante entorno==@env)
- relacionado: ADR 0003 (Compuerta de Modelo, cuyo `MODEL` es el molde de regla mecánica de trigger "siempre" que cae por construcción en el gate de cobertura); ADR 0002 (gate de cobertura fail-closed, rule-agnóstico, que enforza esta regla sin tocar hooks); `brujula/SKILL.md` §4 Topología · «Reglas duras»; `crisol/SKILL.md` §5 catálogo · §2 Roster · §3 punto 6; `crisol/templates/auditor-checklist.md` §D2; `arquitectura/references/deploy-build-once-promote.md` §4-§5-§9

## Contexto

El Paso 0 del Crisol ya fija el **`TARGET:`** de la corrida fail-closed (dónde
corren y se verifican los tests) y, desde 0003, el **`MODEL:`**. El esquema del
TARGET ya admite un **`@env`** (`<env>` ∈ {dev, testing, production}) en la rama
`paas:<proyecto>/<app>@<env>`: declara EN QUÉ entorno vive el recurso. Faltaba
cerrar el lazo: nadie verificaba que el `@env` **declarado** coincidiera con el
entorno **REAL** donde el recurso aterrizó.

El síntoma que destapó el hueco: un deploy declarado `@dev` aterrizó en el
entorno default del `<paas>` (que el `<paas>` llama `production`) sin que el
Crisol lo cazara — el `@env` del TARGET nunca se verificaba contra el entorno
REAL del recurso. El esquema permitía declarar `@dev` y desplegar a otro lado:
la declaración era una etiqueta sin contraste, no un invariante. Un mismatch
silencioso entre lo declarado y lo real es exactamente la clase de divergencia
que el Crisol existe para cazar (la misma familia que "branch inesperado" o
"declaré `opus` pero spawneé `haiku`").

## Decisión

Se establece el invariante **entorno real == `@env` declarado** y se lo hace
machine-checkable, fail-closed, reusando la maquinaria existente (matriz de
veredictos + gate de cobertura de v1.12.0), SIN tocar hooks ni tests:

1. **Extensión del esquema TARGET (`@env` opcional en local).** Además de la
   rama PaaS que ya lleva `@env`, el esquema TARGET admite **`@env` OPCIONAL en
   local**: `docker-local@<env>` / `pc-local@<env>` (`<env>` ∈ {dev, testing,
   production}). Separa la mesa caliente de desarrollo (`@dev`) de un entorno
   local estable de testing. **Sin `@env` = instancia única** (retro-compatible:
   `docker-local` a secas sigue siendo válido y no dispara verificación de env).

2. **Regla nueva `TARGET_ENV`** (clase **H**, híbrida) en el catálogo §5: afirma
   que el env del recurso desplegado == el `@env` declarado en el TARGET. La
   dictamina el `deploy-verifier` (PaaS, vía API read-only) o, para local, el
   `quality-auditor` genérico vía el ítem `[TARGET_ENV]` del checklist §D2 (sin
   API, por disciplina observable).

3. **Caso legal c** (§2 Diseño): extender el contrato del TARGET es **cambio de
   contrato** → tier completo + este ADR. Por eso la extensión del esquema TARGET
   (edición de prosa estable del esquema en `brujula/SKILL.md` y `crisol/SKILL.md`
   §4) está sancionada — no es scope creep, es el caso legal c documentado.

## Frontera y semántica (innegociable)

- **Semántica DINÁMICA: consistencia declarado↔real, jamás impone "dev".** La
  regla afirma que el entorno REAL coincide con el `@env` DECLARADO, cualquiera
  sea ese valor. **NO fuerza "dev"** ni ningún env particular. Una promoción a
  `@testing` o a `@production` declarada y consistente con el recurso real
  **PASA** — la regla protege la promoción, no la obstaculiza. Casos legítimos
  (desarrollo directo en production, proyectos puramente locales) los DEFINE el
  humano al fijar el `@env` en el Paso 0; la regla solo contrasta.

- **Triggers (cobertura dinámica).** `paas:…@<env>` → **DURO** (el
  `deploy-verifier` consulta la API read-only y afirma `recurso.env == @env`).
  `docker-local@<env>` / `pc-local@<env>` → **DISCIPLINA** (sin API; se afirma
  por compose-project / puerto / directorio; mismatch observable → FAIL; sin
  evidencia suficiente → N/A). local-sin-`@env` o TARGET sin `paas:` ni `@env`
  → **N/A** (el trigger no aplica). `N/A` SOLO si el trigger NO aplica.

- **La brújula FLAGEA, no bloquea.** La 4ta fuente de la brújula puede levantar
  una bandera roja temprana (shift-left, read-only) si el recurso vive en otro
  entorno que el `@env`, o si falta el `@env` del proyecto. Es **sugerencia**: el
  humano resuelve en el Paso 0 definiendo el `@env`. La brújula no auto-bloquea
  (hay casos legítimos); el bloqueo fail-closed lo provee el gate de cobertura
  vía `TARGET_ENV` cuando hay mismatch real.

- **Enforcement por construcción (sin tocar hooks).** `TARGET_ENV` se agrega como
  regla a la matriz §5; el `_coverage_state` del `crisol_gate.py` (ADR 0002) es
  rule-agnóstico — exige que toda celda `[V]` con trigger activo sea `PASS`/`N-A`
  con `runState: closing`, sin hardcodear IDs. La regla cae **por construcción**,
  igual que `MODEL` (0003): el parseo del TARGET es presencia-no-esquema
  (`docker-local@dev` ya pasa el hook), y el enforcement de `TARGET_ENV` no
  requiere una sola línea de `crisol_gate.py`, `crisol-enforcer.sh` ni
  `tests/test-enforcer.sh`. Tocar esos `.py`/`.sh` sería scope creep.

## Consecuencias

- **Positivas:** la declaración del `@env` deja de ser una etiqueta sin contraste
  y pasa a ser un invariante verificado; el mismatch "declaré `@dev`, aterrizó en
  el default del `<paas>`" se caza fail-closed; la regla es simétrica con `MODEL`
  y `TARGET` (mismo Paso 0, mismo gate de cobertura, cero superficie nueva en los
  guardianes); la semántica dinámica preserva la promoción (`@testing`/
  `@production` consistentes PASAN); la brújula gana un shift-left read-only sin
  poder de bloqueo (el humano sigue al mando del `@env`).
- **A vigilar:** para local la verificación es de **disciplina** (observable, sin
  API) — sin evidencia suficiente cae a `N/A`, mismo límite honesto que el resto
  de las reglas híbridas; la fila `TARGET_ENV` es load-bearing en la matriz
  cuando su trigger está activo: una corrida `paas:…@<env>` que la omita → FAIL
  del gate de cobertura.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.33.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

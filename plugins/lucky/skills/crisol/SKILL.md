---
name: crisol
description: >-
  El Crisol — Loop de Calidad Incorporada (jidoka) unificado para cambios de
  código. Invocar explícitamente ("/crisol" o "corré el Crisol sobre X") ANTES
  de tocar código que afecte contratos, múltiples archivos o arquitectura.
  Orquesta carriles paralelos por dominio (Planificador → Arquitecto →
  Ingeniero → Verificador), con compuerta compartida del Architecture Steward,
  techo de iteraciones, gate de crédito técnico y run-ledger persistido. NO se
  usa para planificar/charlar — solo para cambios de código.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, Agent, SendMessage, TodoWrite, Write, Edit
---

# El Crisol — Loop de Calidad Incorporada

> Un crisol funde y quema impurezas bajo presión hasta dejar metal puro.
> Esto hace el Crisol con los defectos de un cambio de código.

**Vocabulario ancla (cero jerga inventada):** Cero Defectos (aspiración,
Crosby) · Jidoka / calidad incorporada (mecanismo, Toyota) · Defensa en
profundidad (ya usado en el proyecto) · corrección blameless (Edmondson).

**Fuente canónica:** ADR 0018 (`docs/decisions/0018-crisol-loop-calidad-incorporada.md`).
El Crisol **no inventa roles** — formaliza el Three-Agent Loop (ADR 0007) + el
Architecture Steward, los endurece, los hace paralelos, gateados y enforzados.

---

## 1. Cuándo se invoca (tiers)

El Crisol corre en el **hilo líder** (los subagentes no anidan). El líder lee
esta skill y orquesta los carriles vía Agent Team.

| Tier | Cuándo | Roles que corren |
|---|---|---|
| **Completo** | Código que toca contratos AMQP/REST, >1 archivo, arquitectura, o establece/rompe un patrón | Planificador → Arquitecto → Ingeniero → Verificador (+ Integración si paralelo) |
| **Fast-path** | Cambio trivial: single-file, cosmético, docstring, typo en código | Planificador (mini) → Verificador |

Regla espejo del Steward: *cambios cosméticos no llevan ADR* → tampoco Crisol completo.
**Planificar, leer, charlar, editar docs/.md: NO es Crisol.** El Crisol solo
muerde en código→commit.

---

## 2. Mapeo canónico de roles (1:1 con lo que ya existe)

| Paso (4-pasos de Vikingo) | Rol del proyecto | Veredicto | Permisos |
|---|---|---|---|
| **Planificador** | `<dominio>-archaeologist` (mapea → CURRENT-STATE/CALL-GRAPH/IMPACT-MATRIX) + plan accionable | plan, sin código | read-only |
| **Arquitecto** | **Architecture Steward** (Triage → Zoom-out → Gate de Veto) | `APPROVE` / `REJECT` (= 🚨 VETO) | read-only, no feature code |
| **Ingeniero** | `<dominio>-engineer` (implementa EXACTO lo aprobado, consulta archaeologist por intención) | código *staged*, NO commitea | writes |
| **Verificador** | `<dominio>-quality-auditor` **+** archaeologist (revalidación estructural) — el "AMBOS aprueban" ya existente | `PASS` / `FAIL` | read-only |

Solo `PASS` → commit. `REJECT`/`FAIL` → **vuelve al Planificador** (no se
parchea en caliente).

---

## 3. Adaptación paralela (lo nuevo de fondo)

1. **N carriles por dominio en paralelo.** Naming `<dominio>-<rol>`, equipos
   descartables (NO genéricos). Spawnear teammates con `model: "opus"`.
2. **Archaeologists paralelizan libre** (read-only, carpetas propias).
3. **Compuerta serializada compartida = Architecture Steward.** Ve TODOS los
   planes de todos los carriles ANTES de que cualquier Ingeniero toque código.
   Emite `docs/refactor/_crisol/COLLISION-MAP.md` (plantilla en
   `templates/collision-map.md`) → marca archivos/contratos "calientes" →
   **secuencia los carriles que chocan**. *Poka-yoke: prevenir, no detectar.*
4. **Engineers NO paralelizan sobre archivos compartidos**
   (`docker-compose.yml`, `.env.example`, etc.) — el team-lead los administra.
   Cada engineer corre `git status --short` antes de tocar; si el archivo
   aparece M/A, lee el estado real (no asume).
5. **Verificador de Integración:** tras el doble-gate `PASS` de CADA carril, una
   verificación del resultado **combinado** (lo que pasa aislado puede fallar
   junto: CI serial, archivos compartidos). Recién ahí → commit.

---

## 4. Reglas duras (jidoka)

- **Independencia operacional:** Arquitecto y Verificador reciben SOLO
  artefactos reales (diff, salida de tests que corren ELLOS) — **nunca** la
  prosa del paso previo. Trust but verify.
- **Veredicto binario:** `APPROVE/REJECT`, `PASS/FAIL`. Sin "casi".
- **`FAIL`/`REJECT` → Paso 1.** No hot-patch. Se re-planifica con la corrección.
- **Cero scope creep:** el Ingeniero hace SOLO lo aprobado.
- **Commit solo tras `PASS`** (y `PASS` de Integración si hubo paralelo).
- **Techo de loop = 3 iteraciones.** Si tras 3 ciclos Plan↔REJECT/FAIL no
  converge → el team-lead (deadlock-breaker) **escala a Vikingo** con la
  divergencia exacta. No ciclar infinito.
- **Gate de crédito técnico (REGLA DE ORO):** el Verificador da `FAIL` si el
  cambio toca arquitectura y NO deposita ADR/annotation/IMPACT-MATRIX.
- **Blameless:** la falla se asume inevitable; se exige surface honesto +
  corrección sistémica. No se culpa, se corrige y se registra.
- **Contenedores: terminal = solo lectura.** La terminal dentro de un
  contenedor es SOLO para diagnosticar (logs, probar conexión, mirar). Todo
  cambio real va por la fuente de verdad (Coolify panel/API, o el repo de la
  app): un cambio hecho dentro del contenedor es invisible para Coolify y se
  **pierde en el próximo redeploy**. Si hubo que parchear por terminal
  (emergencia), replicarlo en la fuente de verdad ANTES de cerrar la corrida —
  el Verificador da `FAIL` si queda drift sin replicar.

---

## 5. Run-ledger (memoria del proceso + llave del enforcement)

Cada corrida se registra en `docs/refactor/_crisol/RUN-LEDGER.md` (formato en
`templates/run-ledger.md`). El hook de enforcement (`crisol-enforcer`) **lee
este ledger**: sin entrada `STATUS: ACTIVE` para el branch actual, todo cambio
de código fuente queda **bloqueado**. Apertura/cierre de entrada = disciplina
obligatoria del líder al orquestar el Crisol.

Es ADR 0010 (self-awareness) aplicado al meta-proceso: el sistema acumula su
historial de calidad, no solo el código.

---

## 6. Procedimiento (líder)

1. Clasificar **tier** (completo / fast-path). Trivial → fast-path.
2. Abrir entrada en `RUN-LEDGER.md`: `STATUS: ACTIVE`, branch, tier, alcance,
   carriles.
3. Spawnear **archaeologists** (paralelo, opus) → plan(es) accionable(s).
4. Pasar TODOS los planes al **Architecture Steward** → COLLISION-MAP +
   `APPROVE/REJECT`. REJECT → volver a 3 (cuenta iteración).
5. Spawnear **engineers** por carril respetando la serialización del
   COLLISION-MAP (compartidos los maneja el líder).
6. Cada carril → **quality-auditor + archaeologist** (`PASS/FAIL` sobre estado
   real). FAIL → volver a 3 (cuenta iteración).
7. Si hubo paralelo → **Verificador de Integración** sobre el combinado.
8. Todo verde → commit. Cerrar entrada del ledger: `STATUS: CLOSED` + veredictos
   + iteraciones + escalaciones.
9. Iteraciones > 3 sin converger → `STATUS: ESCALATED` + reportar a Vikingo.

---

## 7. Bootstrap (honesto)

El Crisol no puede dogfoodearse en su propia creación (el loop aún no existía).
Esa única meta-implementación se revisó directo con Vikingo + team-lead, con una
entrada de ledger `BOOTSTRAP` declarada. El primer dogfood real = el siguiente
cambio de código después de existir el Crisol.

---

Checklist del Verificador: `templates/auditor-checklist.md`.

---
id: PLAN-solid
schema: plan/1
tipo: plan
estado: CUMPLIDO
creado: 2026-06-25
refs: [adr:0007]
nota: "materializado por ADR 0007 (SOLID completo: Liskov + ISP + auditoría retroactiva)"
---
# SOLID en el Crisol — plan de integración + auditoría retroactiva (+ demo real)

> **Modo:** investigación PLAN-ONLY (no se implementó nada). Pedido por MLL: *"investiga cómo
> implementar SOLID al Crisol, y una forma de aplicarlo a lo ya hecho."*
> **Generado por:** enjambre de **6 agentes opus** (mapeo · Liskov · ISP · método-retroactivo ·
> demo-código · demo-arquitectura). Ancla: v1.24.0.
> **Estado:** PLAN + hallazgos de demo. Espera decisión de MLL sobre qué bajar.

---

## Resumen ejecutivo

1. **Tu Crisol ya es ~4/5 SOLID por construcción.** S (`ATOMICIDAD`) y O (`OPEN_CLOSED`) de manual;
   D sólido pero **atado a lo hexagonal**; I **parcial**; **L (Liskov) ausente** — único hueco genuino.
2. **Cerrar el gap = 2 reglas nuevas** (`LISKOV`, `INTERFACE_SEGREGATION`), ambas **clase J, gate
   fail-closed** (a diferencia de i18n: SOLID **sí** son defectos), en el **mismo `design-verifier`**
   (cero verificador nuevo). Se bajan con **una corrida Crisol Tier Completo** (los SKILL.md están
   sellados → dispara CREDITO/SELLOS/FORJA).
3. **La auditoría retroactiva NO es una skill nueva ni una corrida del Crisol** — es un **modo
   read-only** homeado como drop-in de `arquitectura`, **independiente** del método de creación pero
   leyendo el **mismo checklist** (fuente única), que **alimenta** al Crisol por dato (IDEAS/bitácora).
4. **La demo funcionó de más:** corrida sobre lucky-skills, cazó **un false-PASS latente en tu propio
   guardián** — corroborado por 2 agentes independientes. El método se probó a sí mismo.

---

# CASO 1 — Meter SOLID al Crisol

## Mapeo: qué cubre HOY (con evidencia)

| SOLID | Regla actual | Estado | Gap |
|---|---|---|---|
| **S** Single-Resp | `ATOMICIDAD` (§2 · §5 `crisol/SKILL.md:468`) | ✅ Cubierto | Casi nulo |
| **O** Open/Closed | `OPEN_CLOSED` + `CASOS_LEGALES` (§2 · §5) | ✅ **El más completo** (la joya) | Ninguno |
| **L** Liskov | — ninguna — | ❌ **Ausente** | Sin regla/ID/verifier |
| **I** Interface-Seg | `CONFORMIDAD` "un puerto por integración" + anti-patrón `Puerto-Dios` | 🟡 **Parcial** | Sin enunciado ISP explícito; condicional a hexagonal |
| **D** Dep-Inversion | `CONFORMIDAD` (deps hacia adentro) + inyección de `ATOMICIDAD` | ✅ **Cubierto** | Fuerte-en-hexagonal, **tenue afuera** |

**Orden de retorno de inversión:** `L` (nuevo) → `I` (subir de parcial) → `D` (desacoplar de hexagonal).

## Regla nueva: `LISKOV` (lista para pegar)

- **§2 «Diseño» (nuevo bullet, tras "Planificar la costura"):** *Sustituibilidad (Liskov):* una
  implementación nueva de una abstracción YA existente (adapter de un puerto, `struct` que llena una
  vtable, función asignada a un puntero-a-función, handler bajo una clave de dispatch, clase que
  `implements`) debe poder ocupar el lugar del supertipo **sin que el llamador se entere**: no
  fortalece precondiciones, no debilita postcondiciones, no obliga a saber cuál impl es. Rompe el
  contrato → `REJECT`, salvo **cambio de contrato declarado en el plan** (caso legal (c) → tier
  completo + ADR). La conformidad de FIRMA la caza el compilador; acá se juzga el contrato **semántico**.
- **§5 catálogo:** `| LISKOV | Implementación nueva de una abstracción existente sustituye al supertipo
  sin romper su contrato | si el diff crea/modifica una implementación de una interfaz/puerto existente | J |`
- **Verificador:** el `design-verifier` pasa a cubrir `OPEN_CLOSED + ATOMICIDAD + COSTURA + LISKOV`
  (input = solo el diff; cobertura dinámica → N/A si no toca una abstracción preexistente; **cero spawn nuevo**).
- **Enforcement: GATE fail-closed** con válvula de plan. Razón: coherente con sus 3 hermanas J que ya
  gatean; el defecto es **polimórfico** (corrompe todos los call-sites en silencio); es defecto de HOY
  (como `RESPONSIVE`), no capacidad futura (como i18n). Camino a clase-H cuando aparezca una rebanada
  decidible-por-código (ej. exhaustividad de handlers).

## Regla nueva: `INTERFACE_SEGREGATION` (lista para pegar)

- **Regla propia, NO enmienda a `CONFORMIDAD`** — ISP es **grano del contrato** (universal: MVC/lib/CLI),
  `CONFORMIDAD` es estructura-macro condicional a hexagonal. Meterla en CONFORMIDAD la sacaría de los
  repos no-hexagonales donde una interfaz gorda igual duele.
- **§2 bullet:** un contrato se parte por **necesidad de cliente**; ningún cliente depende de métodos
  que no usa. La partición es del CONTRATO, no de la impl (el que lo cumple entero puede ser 1 unidad).
  Contrato de N clientes + método que sirve a uno → `REJECT`, salvo justificación (todos usan todo, o
  partir sería especulación). **Distinto de ATOMICIDAD** (SRP = la unidad; ISP = el contrato expuesto a
  clientes — provider-side vs consumer-side).
- **§5:** `| INTERFACE_SEGREGATION | Contrato tajado por necesidad de cliente; ningún cliente depende de
  métodos que no usa | si el diff crea/amplía una interfaz/puerto con ≥2 clientes | J |`
- **`Puerto-Dios`** (`arquitectura/references/anti-patrones.md`) pasa a ser la **instancia hexagonal**
  de esta regla — referenciada por nombre, cero duplicación.
- **Enforcement: GATE fail-closed** (la matriz es binaria; `Puerto-Dios` ya rechaza → degradar a
  advisory dejaría el caso particular más duro que el general).

## Cómo se baja (ambas reglas)

Es un cambio a `crisol/SKILL.md` + `arquitectura/SKILL.md` + `auditor-checklist.md`, todos **sellados**
→ **corrida Crisol Tier Completo** sobre este repo (§6: vN juzga el diff que crea vN+1), que dispara
`CREDITO` (ADR) + `SELLOS` + `FORJA` (`forjar-release.sh vX.Y.Z`). Cero código nuevo en el gate (el
patrón "una fila al catálogo + el verifier emite su línea" — OCP impecable del propio Crisol).

---

# CASO 2 — Auditar lo YA hecho (método retroactivo)

## Forma recomendada: modo read-only, drop-in de `arquitectura`

- **NO skill nueva** (trampa i18n: artefacto con 0 usos = especulación; los jueces rankearon "skill
  nueva" última). **NO corrida del Crisol** (el Crisol gatea código→commit; auditar código viejo NO
  debe gatear — castigar retroactivamente es injusto).
- **SÍ:** un artefacto único `arquitectura/templates/auditoria-solid.md` (procedimiento + rúbrica +
  formato de reporte) + **1 fila al Router** de `arquitectura/SKILL.md`. Es el crecimiento Open/Closed
  que la skill sanciona. Invocable con `/arquitectura` ("auditá SOLID retroactivo de este repo").
- **Independiente del Crisol, pero fuente única compartida:** reusa el `conformidad-checklist.md` como
  definición de los invariantes (no duplica reglas). *Mecanismo separado, criterio compartido* — evita
  el "cisma de guardianes".

## Cómo funciona (detectá → clasificá → priorizá → reportá → alimentá)

- **Detectá** por lente (grep parametrizado al núcleo *descubierto* + juicio LLM): SRP, OCP, LSP, ISP, DIP.
- **Severidad objetiva:** ALTA = *"vive una violación que el gate rechazaría si el código naciera hoy"*
  · MEDIA = real pero localizada · BAJA/SEÑAL = smell sin evidencia.
- **Priorizá** por `severidad × blast-radius × churn` (fan-in + `git log`) — worst-first.
- **Read-only ESTRICTO:** `allowed-tools: Read, Grep, Glob, Bash` (solo lecturas), como `brujula`.
  **Duro con los hechos** (fuente ilegible → N/D, jamás infiere) · **blando con la sanción** (nunca
  bloquea). Espejo de *"la brújula LEE, el Crisol ESCRIBE"*.
- **Alimentación de vuelta (por dato, no por acople):** ALTA → línea a `docs/IDEAS.md` (candidata a
  corrida Crisol) · MEDIA recurrente → `bitacora` CANDIDATE (tipo **DRIFT**: la ley promete SOLID, el
  código lo viola) · BAJA → `SENALES.md` (`visto:N`). **Kaizen:** misma violación en muchos repos =
  **evidencia** para ascender a regla real (`LISKOV`/`ISP` al catálogo) — evidence-triggered, no
  especulativo.
- **Portable** a los ~20 repos: Glob-discovery + N/A-si-ausente, agnóstico a lenguaje, distribuido por
  el mismo plugin `lucky`.

---

# LA DEMO (real, sobre lucky-skills) — el método probándose a sí mismo

## ⭐ Hallazgo estrella (corroborado por 2 agentes independientes)

**Los dos guardianes del Crisol (`crisol_gate.py` + `crisol-enforcer.sh`) dicen "paridad EXACTA" pero
driftearon — y corren juntos en cada Edit/Write.** Es una **violación de Liskov VIVA** (dos
implementaciones de la misma regla, no sustituibles) = el *cisma de guardianes* de v1.11.0 resucitado:

- **False-PASS de branch (el peor):** el gate compara branch **exacto**; el enforcer usa awk
  **substring/regex** (`entry ~ b`) → en branch `main`, una entrada `### main-hotfix …` matchea y
  **abre el gate para el branch equivocado**.
- **Detección de "código" opuesta:** el gate es allow-by-default (fail-open); el enforcer es
  deny-by-default → editar `.gitignore`/`LICENSE`/`.json`/`.png` → enforcer **BLOQUEA**, gate PERMITE.
- **Listas de placeholder mantenidas por separado** (Python set vs awk regex): cercanas, no *probadas*
  idénticas.
- **Fix:** una sola fuente de verdad (que el enforcer delegue en el parser del gate, o extraer
  parse-ledger a un módulo compartido) + que `test-enforcer.sh` corra casos-frontera contra AMBOS.

## Otros hallazgos de código (priorizados)

| # | Principio | Sev | Dónde | Qué |
|---|---|---|---|---|
| 2 | S | MED | `forjar-release.sh` | ~8 responsabilidades en 470 líneas; extraer `classify-skills`/`gen-registry`/`sign-registry` |
| 3 | S/DRY | MED | `crisol_gate.py` + enforcer | parseo del RUN-LEDGER **triplicado** (raíz del drift #1) |
| 4 | D | MED | `adoptar-crisol.sh:14,64` | usa `python` pelado (sin fallback `python3`) → **falla en Linux-solo-python3** ⚠️ bug real |
| 5 | O/DRY | MED | ≥6 archivos | ruta `docs/refactor/_crisol/RUN-LEDGER.md` como constante mágica duplicada |
| 6 | O | BAJA | `crisol_gate.py`, `leak-scan.sh` | taxonomías hardcodeadas, no override por env |

## Hallazgos de arquitectura (priorizados)

| # | Principio | Sev | Dónde | Qué |
|---|---|---|---|---|
| 1 | S | MED | `crisol/SKILL.md` §CD + §Pin-total | dos dominios (release-eng/supply-chain) inline; mover prosa a `references/` |
| 2 | L | MED | `cargar/SKILL.md` vs `registry.schema.json` + hook | **ley↔código drift**: la ley dice "commit informativo, pin-por-commit = deuda v2"; el schema+hook YA pinean por commit. Seguridad *más fuerte* que lo documentado, pero es un FALSO-VERDE conceptual |
| 3 | L/DRY | MED | los 2 guardianes | (corrobora el #1 de código) |
| 4 | I/DRY | BAJA | triggers del roster en §2/§3.6/§4.6 | restated 3×; una tabla canónica + referencias |

## Y lo que YA está SOLID-sano (constructivo, con evidencia)

- **El patrón "cero código nuevo" de la matriz §5** = **OCP impecable**: el gate es agnóstico a las
  reglas (solo verifica `runState: closing` ∧ todo `[V]` ∈ {PASS,N/A}); sumar regla = una fila + un
  verifier. El mecanismo cerrado, el set de reglas abierto.
- **Los `<concern>-verifier` = roster atómico sustituible (Liskov limpio):** mismo contrato
  input=diff/output=veredicto; gate-determinista y verifier-LLM escriben la MISMA línea.
- **Cobertura dinámica = ISP a nivel corrida:** un cambio sin UI jamás paga la interfaz responsive.
- **`cargar` = DIP de manual:** depende de la abstracción `fetch_verify`, cripto invertida fuera del
  modelo, sustituible entre runtimes con degradación **honesta** a MODO MANUAL.
- **`fail-open` del gate ejemplar** (`_allow()` en cada duda, red final `try/except → exit 0`,
  escribir-marcador-ANTES-de-bloquear) · **cero secretos horneados** (leak-scan lo *enforza*) ·
  **adoptar no-destructivo/idempotente** · **"el MÉTODO, no el MAPA"** (DIP aplicada al conocimiento).

---

# Próximos pasos (decisiones para MLL)

Ninguno ejecutado — esto es investigación. Candidatos, de mayor a menor ROI:

1. **🔴 Arreglar el drift de guardianes** (false-PASS de branch + over-block). Es un **bug real** en el
   piso del Crisol, corroborado. Corrida Crisol propia (toca `crisol_gate.py`/enforcer/fixture).
2. **🟠 Arreglar `adoptar-crisol.sh`** (fallback `python3`). Bug real chico, fast-path.
3. **🟢 Bajar `LISKOV` + `INTERFACE_SEGREGATION`** al Crisol (corrida Tier Completo + ADR + forja).
4. **🟢 Construir el modo `auditoria-solid`** (drop-in de `arquitectura`) — y correrlo sobre los ~20
   repos para poblar el backlog con evidencia real.
5. **🔵 Reconciliar el drift ley↔código del pin de `cargar`** (v1 ya pinea por commit; alinear la prosa).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · PLAN + demo (no ley, no ADR). Ancla: v1.24.0.**

---
name: crisol
description: >-
  El Crisol — Loop de Calidad Incorporada (jidoka) para cambios de código.
  Invocar SOLO de forma explícita ("/crisol" o "corré el Crisol sobre X") ANTES
  de tocar código que afecte contratos, múltiples archivos o arquitectura.
  Orquesta carriles paralelos (Planificador → Arquitecto → Ingeniero →
  Verificador) con compuerta del Architecture Steward, veredictos binarios, techo
  de 3 iteraciones, gate de crédito técnico y run-ledger persistido.
  NO usar para planificar, leer, charlar ni editar docs/.md — solo código→commit.
allowed-tools: Read, Grep, Glob, Bash, Agent, SendMessage, TodoWrite, Write, Edit
disable-model-invocation: true
---

# El Crisol — Loop de Calidad Incorporada

Tres ejes, sin excepción: **sencillo** (solo proceso), **objetivo** (todo
veredicto es sí/no o PASS/FAIL), **duro** (nada rompe ni deja deuda técnica).

Corre en el **hilo líder** (los subagentes no anidan). El líder lee esta skill y
orquesta los carriles vía Agent Team. El *porqué* y el mapeo de roles están en
`references/contexto.md` — no hace falta para ejecutar.

---

## 1. Tier (clasificación OBJETIVA)

Respondé el checklist. **Cualquier "SÍ" → Tier Completo.** Todos "NO" → Fast-path.

- [ ] ¿Toca un contrato AMQP/REST?
- [ ] ¿Modifica más de 1 archivo de código?
- [ ] ¿Cambia arquitectura, o establece/rompe un patrón?
- [ ] ¿Toca un archivo compartido (`docker-compose.yml`, `.env.example`, etc.)?

| Tier | Roles que corren |
|---|---|
| **Completo** | Planificador → Arquitecto → Ingeniero → Verificador (+ Integración si hay paralelo) |
| **Fast-path** | Planificador (mini) → Verificador |

**Scope:** solo código→commit.

---

## 2. Reglas duras (jidoka) — innegociables

- **Anti-romper (REGLA 0):** el Verificador corre los tests ÉL MISMO, **EN el
  `TARGET:` declarado** del RUN-LEDGER (el contenedor/host fiel: dev Linux), no
  donde corra el proceso del agente. Sin verde propio → `FAIL` automático. No se
  confía en reporte ajeno. **Jamás en la PC local** salvo `TARGET: pc-local`
  explícito del humano: degradar a local en silencio (target sin responder o sin
  declarar) → `FAIL` fail-closed, no `PASS`; target desconocido → preguntar,
  nunca asumir local. El esquema del target lo define la brújula; acá solo se
  consume.
  Si NO existe suite de tests: registra `TEST_COVERAGE: NONE` en el RUN-LEDGER y
  puede emitir `PASS`, pero el tag estable `vX.Y.Z` queda **bloqueado para
  crearse** mientras siga en `NONE` (es gate de creación: un tag ya existente sí
  puede re-deployarse en rollback).
- **Independencia operacional:** Arquitecto y Verificador reciben SOLO artefactos
  reales (diff, salida de tests propia) — **nunca** la prosa del paso previo.
  En fast-path el Verificador corre en un **contexto nuevo** (subagente fresco):
  el líder NO verifica su propio trabajo. Ese Verificador aplica también los
  criterios de **Diseño** (abajo): violación sin justificación → `FAIL`.
- **Veredicto binario:** `APPROVE/REJECT`, `PASS/FAIL`. Sin "casi".
- **`FAIL`/`REJECT` → Paso 1.** No hot-patch. Se re-planifica con la corrección.
- **Cero scope creep:** el Ingeniero hace SOLO lo aprobado por el Steward.
- **Parking de ideas (anti-olvido):** toda idea, variante o mejora que surja a
  mitad de corrida y esté fuera del scope aprobado se anota AL INSTANTE en
  `docs/IDEAS.md` (una línea: `YYYY-MM-DD · idea · contexto-sin-secretos`) y se
  sigue trabajando. No se implementa, no se discute, no se pierde. Las ideas
  viajan en los WIP-commits, así que sobreviven al crash de sesión.
- **Commit de cierre solo tras `PASS`** (y `PASS` de Integración si hubo
  paralelo). Los WIP-commits no cuentan como cierre — ver §Versionado.
- **Gate de crédito técnico:** si el cambio toca arquitectura y NO deposita
  ADR (`docs/decisions/NNNN-titulo.md`)/annotation/IMPACT-MATRIX → `FAIL`.
- **Migraciones de schema:** si el cambio incluye DDL destructivo (ALTER, DROP,
  tabla nueva), el Planificador registra `MIGRATION_STRATEGY: reversible |
  irreversible + estrategia` en el RUN-LEDGER. Sin ese campo → `REJECT`
  automático. Rollback por tag NO des-migra datos: ante migración irreversible
  decide el humano. Tras su decisión: fix-forward → corrida nueva; revertir DB
  → la ejecuta el humano (código acompañante = corrida nueva); rollback solo de
  código → re-deploy del tag estable anterior.
- **Fuente de verdad:** **dev es la mesa caliente** — ahí se prueba e itera en
  vivo, sin culpa. Pero **testing y producción NO se tocan a mano**: son
  resultado de una promoción. Si algo falla ahí → se vuelve a dev, se corrige,
  pasa el Crisol y se re-promueve. Container de testing/prod = solo diagnóstico.
  **Bug post-release:** el fix-forward es una corrida nueva (entrada `ACTIVE`
  propia); la corrida `CLOSED` no se reabre.
- **Responsive obligatorio (si la corrida toca UI):** toda app/panel/interfaz
  que se cree o modifique debe ser consumible desde **web móvil**. El
  Verificador valida en viewport móvil (~390px): sin overflow horizontal, sin
  cuelgues con datos reales, interacciones usables con touch. **PASS de
  sandbox/desktop NO cuenta como PASS móvil** — UI rota en móvil → `FAIL`.
- **Sin secretos en artefactos:** ningún artefacto del Crisol (RUN-LEDGER, ADR,
  COLLISION-MAP, `IDEAS.md`, mensajes de commit) lleva valores reales de
  credenciales, tokens, passwords, connection strings ni API keys — solo nombres
  de variable, valores ficticios (`<host>`, `example.com`) o `<REDACTED>`. El
  Verificador registra SOLO veredicto + conteo de casos + línea de error si
  FAIL; **prohibido volcar stdout completo de tests** en el ledger.
- **Techo = 3 iteraciones.** Si Plan↔REJECT/FAIL no converge en 3 ciclos → marcar
  `STATUS: ESCALATED` con la divergencia exacta y **DETENERSE**: el agente no
  inicia más ciclos ni busca workarounds; decide el humano. No ciclar infinito.

### Diseño (agnóstico a lenguaje) — criterios de REJECT del Steward

- **Open/Closed:** comportamiento nuevo se **AGREGA** (función/clase/módulo/
  handler nuevo), NO se **EDITA** una unidad estable que ya pasó un Crisol.
  Diff que modifica el corazón de código estable para extenderlo → `REJECT`,
  salvo justificación explícita en el plan (bug fix o refactor deliberado).
- **Atomicidad:** cada unidad (función/clase/módulo) tiene UNA responsabilidad,
  recibe sus dependencias por parámetro/interfaz (cero estado global nuevo), y
  lo grande se arma COMPONIENDO lo chico. Unidad que acumula responsabilidades
  → se divide ANTES de extenderla.
- **Planificar la costura:** el Planificador identifica DÓNDE va a variar el
  sistema y pone ahí el punto de extensión (interfaz, tabla de dispatch,
  registro de handlers). Donde NO hay evidencia de variación → código simple:
  la generalidad especulativa también es deuda.
- **Cuando tocar lo estable es inevitable (3 casos legales):** (a) bug → se toca
  directo, OCP protege comportamiento correcto, no defectos; (b) falta la
  costura → **dos corridas Crisol separadas** (cada una con su entrada `ACTIVE`
  y su techo propio): primero el refactor que abre la costura con comportamiento
  idéntico (verde antes y después), después la extensión entra por la costura;
  (c) cambia el contrato → tier completo + ADR.
- Son **invariantes del diff**, no jerga de framework: valen igual en C (punteros
  a función), C++ (interfaces), desktop Windows, web o scripts. No chocan con
  MVC/capas: MVC organiza lo macro, esto fija el grano de cada pieza.
- **Conformidad estructural (si hay skill de arquitectura):** cuando el repo
  declaró la skill `arquitectura`, el Verificador la **localiza con `Glob`**
  (`**/skills/*/arquitectura/templates/conformidad-checklist.md` o el namespace
  declarado) y la **lee** sobre el diff real — es prosa para un rol LLM, igual
  que `auditor-checklist.md`; el hook `crisol-enforcer.sh` no cambia y sigue
  eximiendo los `.md`. La fuente de verdad de los invariantes es esa skill, no
  este bloque; como recordatorio **no-normativo**: dependencias hacia adentro ·
  núcleo sin I/O · un puerto por integración externa. Violación sin
  justificación en el plan → `FAIL`. Si el `Glob` no encuentra la skill →
  N/A → verde.

### Versionado y promoción por tags (CD)

- **Trunk-based:** una sola rama `main`. **El entorno lo decide el tag, no la rama.**
- **`push` a `main` = respaldo, NO promoción.** Se pushea para no perder trabajo
  (las sesiones son efímeras): tras cada corrida `PASS`, y un **WIP-commit al
  cierre de cada iteración que termina en `FAIL`** (fast-path termina en `PASS`
  directo → solo el commit de cierre). El WIP no es release: solo preserva
  trabajo ante un crash. El código cae en **dev**.
- **WIP-commit seguro:** `git add <archivos-explícitos>` (NUNCA `-A` ni `.`) →
  verificar en `git status` que no entren `.env`, `*.key`, `*.pem`, `*secret*`
  → `git commit -m "wip: crisol iter N"` + push. **Si el push falla** (exit ≠ 0):
  registrar `PUSH_FAILED: <razón>` en el ledger, avisar al humano y continuar —
  el commit local preserva el trabajo; no reintentar en loop.
- **Promover a testing es una decisión aparte y deliberada** (tag `-rcN`), cuando
  el dev lo decide. `push` ≠ `promoción`.
- **`vX.Y.Z-rcN`** → **testing** (candidato a release).
- **`vX.Y.Z`** (semver) → **producción**. Es el release estable.
- **Gate Crisol:** el tag estable `vX.Y.Z` nace SOLO tras una corrida `PASS`
  cerrada en el RUN-LEDGER. **El tag ES el acto de promoción** — no se promueve
  código que no pasó el Crisol.
- **Se promueve lo que se probó:** el tag estable apunta al MISMO commit que pasó
  testing — no se rebuildea código distinto.
- **Tags inmutables:** nunca se mueve un tag publicado. `latest` es el único
  puntero móvil (apunta al último estable). Rollback = re-deployar el tag estable
  anterior.
- **Sellos consistentes (precondición del Gate Crisol):** un release re-sella
  TODAS las skills de la familia al tag nuevo, no solo las de contenido cambiado.
  El bump del sello (`esta copia = tag vX.Y.Z`) es un marcador de versión del
  ritual de release, no comportamiento — re-sellar una skill intacta es un toque
  sancionado (como mover `latest`), NO viola Open/Closed. ANTES de crear el tag
  estable, el Verificador enumera los `SKILL.md` de la familia con `Glob` (igual
  que «Conformidad estructural»), greppea la LÍNEA de sello (`esta copia = tag
  vX.Y.Z`, §6 — no menciones de versión en prosa) y exige EXACTAMENTE una por
  skill, todas == el tag a nacer: conteo ≠ N o algún straggler atrás → `FAIL`, el
  tag no nace. Es chequeo de rol-LLM, no del hook (que sigue eximiendo `.md`).
  **Válvula:** una skill puede llevar sello distinto a propósito
  (congelada/depreciada) SOLO si la divergencia está declarada en el RUN-LEDGER
  (`SELLO_PIN: <skill> @ <tag> · motivo`); sin esa declaración = straggler =
  `FAIL`.

### Pin total (cadena de suministro) — innegociable

- **Pin de TODO lo que consumimos:** cada dependencia externa (librería,
  herramienta, imagen base, GitHub Action, fork upstream) se fija a una versión
  exacta o digest. **Prohibido floating** (`latest`, `main`, `*`, rangos abiertos)
  en lo que CONSUMIMOS. Una promoción ajena JAMÁS debe poder romper nuestro build.
- **Matiz con §tags:** `latest` lo **publicamos** para nuestros propios artefactos;
  **nunca lo consumimos** de un tercero.
- **Fork = propiedad nuestra:** si forkeamos y modificamos un upstream, lo
  mantenemos NOSOTROS. El fork vive en **nuestro** repo (fuente de verdad), no como
  dependencia viva del upstream.
- **Copia propia de lo crítico:** mantener mirror/vendor de aquello que un
  takedown o un cambio ajeno nos rompería. Si nos puede tumbar, lo tenemos nosotros.
- **Cambio de pin = corrida Crisol.** Bump de parche/seguridad que no toca
  contratos → **fast-path** con `BUMP_REASON: <vieja> → <nueva>` en el ledger.
  Bump minor/major → tier completo; brief del archaeologist: changelog entre
  versiones, breaking changes declarados, impacto en contratos propios.

---

## 3. Paralelo (poka-yoke: prevenir, no detectar)

1. **N carriles por dominio.** Naming `<dominio>-<rol>`, equipos descartables.
   Model por TIER según COMPLEJIDAD (mapeo único al pie de esta skill):
   tarea mecánica → tier-económico · juicio/decisión (Steward, Verificador de
   Integración) → tier-alto · síntesis súper-compleja → tier-frontera.
   El tier barato en tarea compleja sale CARO (rework). **Declarar los tiers
   elegidos al humano ANTES de spawnear.**
2. **Archaeologists paralelizan libre** (read-only, carpetas propias).
3. **Compuerta serializada = Architecture Steward.** Ve TODOS los planes ANTES de
   que cualquier Ingeniero toque código. Emite COLLISION-MAP, marca calientes,
   secuencia los carriles que chocan, y aplica los criterios de **Diseño** (§2)
   a cada plan. **Dos planes que tocan el mismo contrato → `REJECT` a ambos;
   re-planificar consolidando el contrato en UN solo plan.**

   Si el repo declaró la skill de arquitectura (presencia del namespace
   `arquitectura`/`lucky:arquitectura`), el Steward la consulta para juzgar la
   **estructura** del plan: dónde cae cada pieza, naming y capa. El Steward NO
   redefine la estructura: la lee de la skill. Sin skill instalada → solo los
   criterios de Diseño (§2).
4. **Archivos compartidos se serializan:** el carril prioridad-1 del COLLISION-MAP
   los toca primero; el líder pasa ese estado ya modificado como base al carril
   siguiente, y valida ausencia de pisadas antes del Verificador de Integración.
   Cada engineer corre `git status --short` antes de tocar; si aparece M/A
   inesperado, lee el estado real (no asume).
5. **Verificador de Integración:** tras el doble-gate `PASS` de CADA carril,
   verifica el resultado **combinado**. Recién ahí → commit.

---

## 4. Procedimiento (líder)

**Fast-path:** 0 → 1 → 2 → Planificador (mini) → Verificador (subagente fresco)
→ 8. Se saltan los pasos 3–7.

0. Sesión nueva o retomada → correr la skill **brujula** (namespace según
   instalación: `/brujula` o `/lucky:brujula`) para anclar el estado real.
   Con red: verificar la vigencia de la ley (§6 "Ley viva").
   Todo `N/D` → continuar, no bloquea. Working tree sucio → decidir y registrar:
   WIP-commit (si es trabajo recuperable) o `git reset --hard` (si es basura de
   crash); sin árbol limpio NO se abre `ACTIVE`. ¿Brújula reporta huérfana
   `ACTIVE`? → resolverla en el paso 2 antes que nada.
   Fijar el **`TARGET:`** de la corrida (dónde corre/verifica — lo consume la
   REGLA 0, §2) ANTES de abrir `ACTIVE`. La brújula ya ancla la topología de
   deploy (4ta fuente) y **sugiere/prefillea** el target; el Crisol lo **consume**
   y lo **confirma con el humano** en UNA pregunta de 1 tecla (Enter acepta el
   sugerido) — no re-deriva ni consulta la API por su cuenta (esa mecánica es de
   la brújula). Esquema: `paas:<proyecto>/<app>@<env>` (`<env>` ∈ {dev,testing,
   production}; dev = mesa caliente, default) | `docker-local` (contenedor Linux
   fiel) | `pc-local` (la PC del dev, Windows). **Fail-closed:** brújula reporta
   `N/D` o el target es ambiguo → **PREGUNTAR y esperar** (sin humano: ABORTAR),
   jamás asumir local. `pc-local` NO es el default: solo si el humano lo pide
   explícito. El target confirmado se registra en el paso 2.
1. Clasificar **tier** con el checklist §1. Todos NO → fast-path.
2. `git fetch && git rebase origin/main` (conflicto → resolver antes de seguir;
   prohibido `--force` en `main`). Abrir entrada en
   `docs/refactor/_crisol/RUN-LEDGER.md` — crear directorio/archivo si no
   existen, con los campos mínimos:
   ```
   ### <branch> — <YYYY-MM-DD>
   - STATUS: ACTIVE
   - Tier: <completo|fast-path>
   - Fecha: <YYYY-MM-DD>
   - TARGET: <paas:<proyecto>/<app>@<env> | docker-local | pc-local>
   ```
   (plantilla completa: `templates/run-ledger.md`, si existe).
   **Huérfana `ACTIVE` previa:** reportarla al humano (Fecha · Tier ·
   iteraciones N · WIP-commits) y esperar su decisión — **reanudar** (si hay
   COLLISION-MAP `APPROVE` → saltar al paso 5; techo restante = 3−N) o
   **reiniciar** (cerrarla `ESCALATED · Motivo: crash-de-sesión · Iter: N ·
   WIP: <hashes>` → paso 3). Si N ≥ 3 → solo `ESCALATED`, no se reanuda.
3. Spawnear **archaeologists** (paralelo, sonnet) → plan(es) accionable(s).
4. Pasar TODOS los planes al **Architecture Steward** → COLLISION-MAP
   (`templates/collision-map.md`) + `APPROVE/REJECT`. REJECT → volver a 3 (cuenta iteración).
5. Spawnear **engineers** en el orden del COLLISION-MAP: engineer-A → esperar su
   `PASS` de auditor → recién entonces engineer-B. Carriles sin archivos
   compartidos corren en paralelo.
6. Cada carril → **quality-auditor + archaeologist** sobre estado real
   (`templates/auditor-checklist.md`) → `PASS/FAIL`. FAIL → volver a 3 (cuenta iteración).
7. Si hubo paralelo → **Verificador de Integración** sobre el combinado; por
   cada archivo caliente del COLLISION-MAP, verificar que los cambios de todos
   los carriles convivan (sin sobreescrituras entre sí).
8. Todo verde → commit. Cerrar entrada: `STATUS: CLOSED` + veredictos +
   iteraciones + `RETRO:` una línea sobre la fricción del PROCESO (blameless:
   se registra la falla, no el culpable). En el resumen de cierre, listar las
   ideas capturadas en `docs/IDEAS.md` durante la corrida.
   - Si la corrida habilita un release → el tag estable `vX.Y.Z` se crea recién
     con `STATUS: CLOSED` + `PASS` (§Versionado). Rollback = tag anterior; los
     tags son inmutables.
9. Techo de iteraciones → §2.

---

## 5. Run-ledger (llave del enforcement)

El ledger es obligatorio **con o sin hook instalado** — el hook automatiza el
enforcement, no lo origina. Cada corrida se registra en
`docs/refactor/_crisol/RUN-LEDGER.md`. El hook `hooks/crisol-enforcer.sh`
(PreToolUse Edit|Write) lo lee: **sin entrada `STATUS: ACTIVE` para el branch
actual, todo cambio de código fuente queda bloqueado (exit 2).** Docs/.md quedan
exentos. Conectarlo con `hooks/settings.snippet.json` en `.claude/settings.json`.

**Invariante: exactamente UNA entrada `ACTIVE` por branch**, con los campos
mínimos del paso 2 — incluido `TARGET:` (dónde corre/verifica la corrida; lo fija
el Paso 0). Una línea suelta con `ACTIVE` no habilita nada (el hook lo valida).
**Fast-path:** basta la entrada mínima con `Tier: fast-path`, sin
COLLISION-MAP ni Steward — dev sigue siendo mesa caliente con ceremonia de 30
segundos. **Excepción DDL:** si el diff contiene `ALTER`/`DROP`/`CREATE TABLE`,
la entrada (incluso fast-path) debe llevar `MIGRATION_STRATEGY` — sin él →
`FAIL` del Verificador.

---

## 6. La ley se gobierna a sí misma

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.10.2` (cache local, NO la ley).** **Ley viva:** al invocar la skill, si la
sesión tiene red: `git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git` — si existe un tag mayor al de
esta copia, descargar y seguir LA DEL REPO
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/crisol/SKILL.md`)
e informar al humano. Sin red: seguir esta copia y registrar
`LEY: <tag> (local, sin verificar)` en la entrada del ledger.

Este skill es ciudadano de su propia ley:
cambiarlo = corrida Crisol EN ese repo, juzgada por la **versión vigente**
(último tag) — vN juzga el diff que crea vN+1; la regresión muere por
estratificación temporal. Promoción del skill = tag semver + subida a las
superficies. Disparador kaizen: ~3 `RETRO:` apuntando a la misma regla → se
abre la corrida sobre el propio skill.

---

**Mapeo de tiers (actualizar SOLO acá cuando cambien los modelos):**
económico=`sonnet` · alto=`opus` · frontera=`fable`

**Templates:** `templates/collision-map.md` · `templates/run-ledger.md` · `templates/auditor-checklist.md`
**Hook:** `hooks/crisol-enforcer.sh` (+ `hooks/settings.snippet.json`)
**Fundamento / roles:** `references/contexto.md`

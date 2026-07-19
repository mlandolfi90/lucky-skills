---
name: saber
description: >-
  Saber — administra el ciclo de vida del conocimiento central (repo
  `lucky-saber`, tools MCP `saber_*`): estado del ciclo, revisar la bandeja
  inbox → merge con endoso, promoción CANDIDATE→LIVE y poda guiadas, y destilar
  al CIERRE de una corrida (spawnea al agente `destilador`). Disparar cuando el
  operador diga "/saber", "revisá la bandeja del saber", "promové/podá una
  ficha", "destilá el cierre", o al cerrar una corrida con disparador objetivo.
  NO disparar para consultar un patrón por síntoma (eso es la skill `bitacora`)
  ni para capturar una idea a futuro (eso es /idea). Administra el ciclo; no
  consulta ni redacta el catálogo.
allowed-tools: Read, Grep, Glob, Bash, Agent
---

# Saber — administrar el ciclo del conocimiento central

La `bitacora` **consulta** (síntoma → acción) y **captura**; el Crisol **decide**
si está bien hacer algo. El **saber** administra el CICLO del conocimiento
central que nadie administraba: la bandeja `mcp-inbox` → merge → CANDIDATE→LIVE →
poda/ascenso, y la destilación al cierre de una corrida.

**El enemigo: documentar sin aprender** — la lección que quedó guardada en un
RETRO sellado o en el parking y NO vuelve cuando el síntoma vuelve, porque solo
la bitácora **LIVE** se consulta por síntoma. Guardar es documentar; que el
sistema te la devuelva sola es aprender. Esta skill cierra ese lazo sin fingir
autoridad que no tiene: la gobernanza (qué es verdad, qué entra a main) es del
operador, ficha por ficha.

**Ejes:** administra (no consulta ni redacta) · endoso POR FICHA (jamás batch) ·
nunca finge una capacidad que el MCP no da · `docs/IDEAS.md` es la bandeja local
(append-only) · fail-open sin MCP (nada se pierde, nada bloquea).

**Frontera con `bitacora` (fuente única, PIN 2):** todo lo de CONSUMIR (buscar/
ficha por síntoma), la DOCTRINA de captura (§Capturar) y el ESPEJO local
(`INDEX.md`/`entries/`/`SENALES.md`, READ-ONLY generado) vive en `bitacora` y NO
se re-enuncia acá: se referencia por nombre. Esta skill solo ADMINISTRA el ciclo.

**Sin el MCP en la sesión** (las tools `saber_*` no están): **fail-open
declarado** — cada subcomando degrada a lo que se puede leer/parkear localmente,
lo dice explícito ("saber MCP ausente: …") y NUNCA bloquea ni inventa un
resultado del catálogo.

---

## `/saber` — estado del ciclo (read-only)

Reporte compacto del ciclo, sin tocar nada:

1. **LIVE + CANDIDATE-en-main:** `saber_index` (default, LIVE) y
   `saber_index(incluir_candidate=true)` — cuántas fichas vivas, cuántas
   CANDIDATE ya mergeadas a main esperando promoción.
2. **Salud/uso:** `saber_metricas` — `consultas` y `citas_causales_alegadas` por
   entrada (asesor de la promoción, no la ejecuta).
3. **Propuestas sin mergear (bandeja local):** grep de `docs/IDEAS.md` por las
   líneas de parking `saber: propuesta pendiente` — las fichas propuestas al
   inbox que todavía nadie endosó.
4. **Reportá** en un bloque: `LIVE: N · CANDIDATE-en-main: N · propuestas sin
   mergear: N` + cualquier **discrepancia** que salte (p. ej. una propuesta
   parkeada cuya rama ya no aparece — señal, no acción).

Sin MCP → reportá solo la bandeja local del grep y declaralo ("saber MCP
ausente: solo bandeja local").

## `/saber revisar` — bandeja → merge (SOLO con el operador presente)

Merge de propuestas a main del saber, **ficha por ficha, con endoso explícito**.
Dos fuentes:

- **(a) Propuestas SIN mergear** — las líneas de parking de `docs/IDEAS.md`:
  `saber: propuesta pendiente mcp-inbox/<hash> · <síntoma>`. **LÍMITE REAL
  documentado (arqueología ADR 0023):** NINGUNA tool MCP enumera las ramas
  `mcp-inbox/*`; el `branch` que devuelve `saber_proponer_ficha` es el ÚNICO
  handle para mergearla. Por eso cada propuesta se persiste como línea de
  parking: es la bandeja. Una propuesta cuyo branch se perdió (nunca se parkeó,
  o se borró la línea) es **invisible vía MCP** — se declara como tal, no se
  inventa.
- **(b) CANDIDATE ya en main** — `saber_index(incluir_candidate=true)`: las que
  ya se mergearon y esperan promoción a LIVE (eso es `/saber promover`).

Procedimiento (fuente a):

1. Recolectá las líneas de parking pendientes.
2. **FICHA POR FICHA**, presentá al operador la ficha con su **evidencia** (el
   síntoma y la ref del parking) y esperá un **endoso EXPLÍCITO** de ESA ficha.
3. Endoso → `saber_mergear(branch)` de ESA ficha (solo anexa CANDIDATE nuevas,
   fast-forward; nunca promueve a LIVE).
4. Tras el merge → marcá la propuesta como saldada con una **línea nueva** vía el
   flujo /idea: `saber: mergeada <branch>`. **`docs/IDEAS.md` es append-only:
   JAMÁS se edita ni se borra la línea vieja** (la propuesta pendiente queda como
   historia; la nueva la salda).
5. **Rechazo** → se descarta anotando el porqué (línea nueva de parking:
   `saber: descartada <branch> · <motivo>`). No se mergea.

**PROHIBIDO BATCH:** un "sí" no es un "sí al lote". Cada ficha exige su propio
endoso; jamás infieras endoso de contexto ni mergees varias de una.

Sin MCP → presentá las fichas parkeadas para lectura y declará que el merge
requiere el connector ("saber MCP ausente: no se puede mergear, quedan en la
bandeja").

## `/saber promover <ID>` y `/saber podar` — GUIADOS v1 (sin tool MCP)

**Por diseño no hay tool que ejecute esto** (arqueología ADR 0023):
`saber_mergear` nunca promueve a LIVE, y el MCP nunca escribe `usos`/`estado`/
`scope`. Estos subcomandos son **guiados**: la skill PRESENTA y registra el
endoso; el **ACTO lo ejecuta el operador** en el repo `lucky-saber`. La skill
JAMÁS finge una capacidad que el MCP no da.

- **`/saber promover <ID>`** (CANDIDATE→LIVE): presentá la ficha — cuerpo con
  `saber_ficha(<ID>)`, uso con `saber_metricas(<ID>)` — y el criterio (evidencia
  real, `usos`). Registrá el endoso del operador y **decilo claro**: "promover a
  LIVE es un acto en `lucky-saber` (git); esta skill no lo ejecuta".
- **`/saber podar`**: presentá los candidatos a poda/ascenso con los criterios de
  `bitacora` §Mantener — **STALE >90 días**, **usos bajos**, **tope ~40 entradas
  vivas**; ascenso (patrón `usos ≥ 3` o explicado en >2 RETROs → puntero a ADR/
  skill/regla). Registrá el endoso; el acto (archivar con su razón, o ascender)
  lo ejecuta el operador en `lucky-saber`.

## `/saber destilar <refs>` — el gatillo del cierre de corrida (crisol §4 paso 8)

El acto de aprender al cerrar una corrida CON disparador objetivo:

1. **Spawneá al agente `destilador`** POR NOMBRE (vía `Agent`), con:
   `{REPO}` = este repo; `{ARTEFACTOS}` = `<refs>` (fila de corrida + RETRO,
   veredictos, postmortems, diagnósticos, microfixes); `{SINTOMAS_PREVIOS}` =
   los síntomas de `saber_index` (para que declare posibles duplicados).
2. **Recibí sus borradores** (o `NADA COSECHABLE: <por qué>` — que se **respeta**:
   no se re-spawnea al destilador para "insistir").
3. **Por cada borrador**, validá con `saber_gate_check(...)` — **dry-run, cero
   side effects**: dice si pasaría el gate (lint + leak-scan) o qué lo rechaza.
4. **Los que pasan** → proponelos con `saber_proponer_ficha(...)` (→ rama
   `mcp-inbox/*`, **JAMÁS main**). Proponer al inbox es el **ÚNICO acto sin
   endoso** — no toca main, por construcción del MCP.
5. **Parkeá cada propuesta** con el `branch` DEVUELTO, vía el flujo /idea:
   `2026-… · saber: propuesta pendiente <branch> · <síntoma corto> · endosar con
   /saber revisar`. Sin esa línea la propuesta es invisible (ver `/saber
   revisar`, límite real).
6. **Reportá** qué propusiste (con su branch) y qué NO (con el porqué del gate).

**Sin MCP en la sesión** → los borradores del destilador van **ÍNTEGROS a
`/idea`** (parking local, "síntoma → acción" + evidencia), para proponerlos al
saber desde una sesión con el connector. Nunca se pierden, nunca bloquean.

---

## Reglas duras

- **Endoso POR FICHA** (directiva del operador 2026-07-17): TODO merge/promoción/
  poda exige endoso explícito de ESA ficha. **Jamás batch** — un sí no es un sí
  al lote; jamás se infiere endoso de contexto.
- **Jamás fingir una capacidad que el MCP no da.** Promover y podar no tienen
  tool: son guiados, el acto es del operador en `lucky-saber`. Enumerar
  `mcp-inbox/*` no tiene tool: la bandeja es el parking local.
- **El espejo local de `bitacora` NO se toca** (`INDEX.md`/`entries/`/
  `SENALES.md` son READ-ONLY generados desde el saber): una edición a mano se
  pierde en la próxima regeneración.
- **`docs/IDEAS.md` solo por append** — se agregan líneas (propuesta pendiente,
  mergeada, descartada); jamás se edita ni se borra una línea vieja.
- **Cero secretos en fichas y reportes** (leak): nombres de variable, nunca
  valores; `<host>`/`<REDACTED>`; rutas relativas, nunca absolutas con usuario.
- **`NADA COSECHABLE` se respeta:** no se re-spawnea al destilador para insistir;
  una cosecha honestamente vacía es un resultado válido.
- **El proponer al inbox no toca main** (rama `mcp-inbox/*`): por eso es el único
  acto que el flujo dispara sin endoso. Todo lo demás espera al operador.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/saber/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe pero
NO incluye `saber/` (la skill nació en este bump), tratar como sin-red — seguir
esta copia y registrar `LEY: <tag> (local, skill nueva sin verificar)`. Sin red:
seguir esta copia.

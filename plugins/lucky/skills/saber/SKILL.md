---
name: saber
description: >-
  Saber — administra el ciclo de vida del conocimiento central (repo
  `lucky-saber`, tools MCP `saber_*`): estado del ciclo, la ventana de gracia de
  la evidencia-cero, la CURADURÍA del catálogo (consolidar + fusionar
  cuasi-duplicados + podar), citar las fichas que funcionaron, y capturar al
  CIERRE de una corrida (spawnea al agente `destilador`, ahora hacia LIVE
  directo). Disparar cuando el operador diga "/saber", "curá/destilá el
  catálogo", "fusioná los duplicados del saber", "podá una ficha", "citá las
  fichas que funcionaron", o al cerrar una corrida con disparador objetivo.
  NO disparar para consultar un patrón por síntoma (eso es la skill `bitacora`)
  ni para capturar una idea a futuro (eso es /idea). Administra el ciclo; no
  consulta ni redacta el catálogo.
allowed-tools: Read, Grep, Glob, Bash, Agent
---

# Saber — administrar el ciclo del conocimiento central

La `bitacora` **consulta** (síntoma → acción) y **captura**; el Crisol **decide**
si está bien hacer algo. El **saber** administra el CICLO del conocimiento
central que nadie administraba: la **captura que entra LIVE directo**, la
**CURADURÍA** humana (consolidar + fusionar cuasi-duplicados + podar la
evidencia-cero) y el **refuerzo** por cita.

**Fase 2 (ADR 0028).** La ficha se sirve **al capturarse** — se elimina el estado
`CANDIDATE` y el gate pre-LIVE. El principio "el humano decide qué es verdad" NO
muere: se **MUEVE** del juicio pre-LIVE a la **curaduría posterior** (`/saber
destilar`) + el override manual (`endosar.py`). Cambia el momento del juicio, no
su existencia.

**El enemigo: documentar sin aprender** — la lección que quedó guardada y NO
vuelve cuando el síntoma vuelve. Guardar es documentar; que el sistema te la
devuelva sola es aprender. Esta skill cierra ese lazo sin fingir autoridad que no
tiene: el juicio (qué se fusiona, qué se poda) es del operador, en la curaduría.

**Ejes:** administra (no consulta ni redacta) · el juicio humano vive en la
**CURADURÍA batch** (cada fusión y cada poda con confirmación de ESE ítem, jamás
auto) · nunca finge una capacidad que el MCP no da · `docs/IDEAS.md` es la bandeja
local (append-only) · fail-open sin MCP (nada se pierde, nada bloquea).

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

1. **LIVE:** `saber_index` — cuántas fichas vivas se sirven. (Ya no hay
   `CANDIDATE` para fichas: la captura entra LIVE directo — ADR 0028.)
2. **Salud/uso:** `saber_metricas` — `consultas` y `citas_causales_alegadas` por
   entrada. Una ficha LIVE con **0 citas + `usos`=0** y edad ≥ ~30d está en la
   **ventana de gracia de la evidencia-cero**: candidata a poda (ver `/saber
   podar`), NO a promoción — la promoción ya no existe.
3. **Parking local (bandeja offline):** grep de `docs/IDEAS.md` por las líneas de
   parking `saber:` — lo capturado/citado offline que todavía no llegó al
   catálogo (fail-open sin MCP).
4. **Reportá** en un bloque: `LIVE: N · evidencia-cero (~30d): N · parking local:
   N` + cualquier **discrepancia** que salte (señal, no acción).

Sin MCP → reportá solo la bandeja local del grep y declaralo ("saber MCP
ausente: solo bandeja local").

## `/saber revisar` — override excepcional (NO puerta de entrada)

En Fase 2 la captura entra LIVE directo: **`/saber revisar` deja de ser la puerta
de entrada al catálogo** (el estado `CANDIDATE` se eliminó para fichas — ADR
0028). Sobrevive SOLO como **override humano excepcional**:

- **Corregir el catálogo a mano** — `endosar.py` (repo `lucky-saber`, fuera del
  MCP): el override manual del humano sobre una ficha LIVE.
- **Ideas / señales / legacy** — `saber_mergear(branch)` sigue vivo SOLO para
  mergear ideas/señales o una `CANDIDATE` legacy en vuelo (las que quedaron antes
  del flip). **Ficha por ficha, con endoso explícito de ESA ficha** — el portón
  de endoso no se borra: se reserva al override, jamás se infiere del contexto ni
  se mergea al lote.

No es un paso del ciclo normal. Sin MCP → declaralo ("saber MCP ausente: el
override requiere el connector, o `endosar.py` en `lucky-saber`").

## `/saber promover` — DEROGADO como paso de ciclo (ADR 0028)

**Ya no existe la transición `CANDIDATE→LIVE`:** la captura entra LIVE directo,
así que no hay ficha que "promover". El acto humano de juicio se **MOVIÓ** a la
**curaduría** (`/saber destilar`: fusión + poda con confirmación) y al **override**
(`endosar.py`). Si alguien pide "promover una ficha", reencuadralo: o ya está LIVE
(se sirve), o es una `CANDIDATE` legacy en vuelo (mergear vía `/saber revisar`
override), o querés corregirla a mano (`endosar.py`). La skill JAMÁS finge una
promoción que el modelo ya no tiene.

## `/saber podar` — la ÚNICA garganta de poda (propone → el humano confirma)

La poda de **salida** reemplaza al gate de **entrada** (ADR 0028): lo que a ~30d
no juntó ni una cita ni un uso, sale. Es la **única garganta de poda** del saber
(no se reimplementa en ningún otro lado):

1. **Proponé read-only** con `saber_destilar_proponer(modo='poda', dias_poda=30)`:
   devuelve los **podables** — la evidencia-cero (**0 citas + `usos`=0 + edad ≥
   ~30d**). La tool NO archiva: **PROPONE** (READ-ONLY, sin side effects).
2. **POR FICHA**, presentá al humano el candidato con su **historial**
   (`saber_historial(entry_id)`: ts · veredicto · sesión · run_ledger_ref ·
   contexto; **0 citas = `SERVIDA SIN PROBAR`**) y esperá su confirmación de ESA
   ficha. Jamás batch, jamás auto-poda.
3. **Confirmado** → el archivar es **reversible** (`estado=archivado`, NO borrado:
   el por-qué-se-jubiló también es conocimiento; se restaura). El MCP propone; el
   acto de archivar lo aplica el humano vía el override (`endosar.py`,
   `lucky-saber`) — la skill no finge un write que el MCP no da.

Sin MCP → presentá lo que puedas leer y declará que el cómputo de podables
requiere el connector ("saber MCP ausente: no se pueden proponer podables").

## `/saber destilar` — el RITUAL de curaduría humana batch (Fase 2)

El acto de juicio humano que **MOVIÓ acá** (ADR 0028): consolidar y limpiar el
catálogo LIVE. Tres pasos, todos **propone → el humano confirma** (jamás auto):

1. **Consolidar** — leé el catálogo LIVE (`saber_index`) y, por ficha de interés,
   su **historial** (`saber_historial(entry_id)`: ts · veredicto · sesión ·
   run_ledger_ref · contexto; **0 citas = `SERVIDA SIN PROBAR`**). Es la foto de
   qué se sirve y qué probó funcionar.
2. **Fusionar cuasi-duplicados** — `saber_destilar_proponer(modo='fusiones',
   umbral_causa_accion=0.80)` PROPONE los pares candidatos (causa+acción lado a
   lado + 2 scores; `veredicto_sugerido` SIEMPRE `REVISAR`). **REGLA DE FUSIÓN
   (horneada, insumo de RAG):**
   - **Discriminante = CAUSA-RAÍZ + ACCIÓN**, jamás el síntoma ni el vocabulario.
     Lo que "suena" parecido casi siempre es **complementario** (vinculado por
     `refs:`), no duplicado (12 escépticos opus: 0/12 cuasi-dups aparentes debían
     fusionarse).
   - **Default ante duda = NO fusionar.** La fusión es **irreversible** y destruye
     conocimiento: en la duda, se deja separado.
   - **El comando PROPONE, nunca fusiona solo.** El humano confirma **CADA**
     fusión; la UX muestra **causa+acción de cada par** para juzgar por lo que
     importa, no por cómo suena.
3. **Podar la evidencia-cero** — vía `/saber podar` (la única garganta de poda; no
   se reimplementa acá): propone los evidencia-cero a ~30d, el humano confirma,
   reversible = archivar.

Cadencia **barata**: sugerida al cierre de corrida o por umbral acumulado. El
núcleo de valor es la fusión (los duplicados exactos ya los dedup el `content_key`
en captura). Sin MCP → declaralo: la curaduría necesita el connector para
proponer.

## `/saber capturar <refs>` — la captura al CIERRE de corrida (crisol §4 paso 8)

El acto de aprender al cerrar una corrida CON disparador objetivo (antes se
llamaba `/saber destilar`; **renombrado** en Fase 2 para no colisionar con la
curaduría):

1. **Spawneá al agente `destilador`** POR NOMBRE (vía `Agent`), con:
   `{REPO}` = este repo; `{ARTEFACTOS}` = `<refs>` (fila de corrida + RETRO,
   veredictos, postmortems, diagnósticos, microfixes); `{SINTOMAS_PREVIOS}` =
   los síntomas de `saber_index` (para que declare posibles duplicados). El
   destilador sigue **CAPTURADOR read-only** (ADR 0023): devuelve borradores, no
   escribe.
2. **Recibí sus borradores** (o `NADA COSECHABLE: <por qué>` — que se **respeta**:
   no se re-spawnea al destilador para "insistir").
3. **Por cada borrador**, validá con `saber_gate_check(...)` — **dry-run, cero
   side effects**: dice si pasaría el lint + leak-scan o qué lo rechaza.
4. **Los que pasan** → `saber_proponer_ficha(...)` — semántica Fase 2 (ADR 0028):
   **captura y SIRVE LIVE en main directo** (ACK `capturada`, id
   `CAP-<content_key>`), ya **no** a `mcp-inbox/*`. La captura fresca se sirve
   `SERVIDA SIN PROBAR`: su colchón es el historial de citas + la poda de
   evidencia-cero, no un gate pre-LIVE (trade honesto — ADR 0028).
5. **Reportá** qué capturó LIVE (con su id `CAP-…`) y qué NO (con el porqué del
   gate).

**Sin MCP en la sesión** → los borradores del destilador van **ÍNTEGROS a
`/idea`** (parking local, "síntoma → acción" + evidencia), para capturarlos desde
una sesión con el connector. Nunca se pierden, nunca bloquean el cierre.

## `/saber citar <refs>` — el REFUERZO del cierre de corrida (crisol §4 paso 8)

El **gemelo** de `/saber capturar` en el gatillo del cierre: la captura cablea qué
ficha NUEVA nace, esto cablea el REFUERZO (¿qué ficha EXISTENTE funcionó de
verdad?). En Fase 2 la cita alimenta el **HISTORIAL** de la ficha
(`saber_historial`), no una promoción: registra la **cita causal ALEGADA** — un
*claim*, no un ascenso. **Jamás mueve `usos` ni promueve** (no hay promoción que
asesorar: la ficha ya se sirve LIVE — ADR 0028):

1. **Reuní las fichas que ESTA sesión consultó** — las que el agente miró con
   `saber_buscar`/`saber_ficha` en el hilo, más las que un **verificador canónico
   aplicó como doctrina** (ej. el `quality-auditor` aplica `FALSO-VERDE-004`/
   `DRIFT-007` al correr REGLA 0). No hay tool de "consultas de esta sesión": el
   insumo es el hilo del agente + las fichas que los roles nombran en su prompt.
   **Degradación por compactación (declarada, NO silenciosa):** el "el agente
   recuerda qué consultó" se **ROMPE** con la compactación de contexto — un hilo
   largo pierde las consultas tempranas. Mientras NO exista un rastro server-side
   por sesión, no dependas de la memoria en silencio: presentá las fichas que
   PUEDAS reconstruir, **pedile EXPLÍCITO al humano que agregue las que se hayan
   olvidado**, y **declará la limitación** ("memoria de sesión posiblemente
   incompleta por compactación"). Cuando el rastro server-side exista, `/saber
   citar` lo lee y esta degradación desaparece.
2. **POR FICHA**, presentá al humano cuál PARECE haber funcionado y esperá su
   **confirmación** (principio de endoso: **el humano decide qué es verdad**; el
   LLM no se auto-adjudica que la ficha funcionó). Jamás batch.
3. **Pasá el `entry_id` que viste — el server resuelve la identidad estable.**
   Registrá cada ficha confirmada con `saber_telemetria` pasando el **`entry_id`**
   (el id-display que viste: `GAP-nnn`, `CAP-xxx` o un `CAND-xxx` legacy). **El
   server lo resuelve internamente a su clave estable `content_key`**
   (`sha256(síntoma·\x00·acción)`, recomputable al servir) y **coalesce las citas
   a través del rename** (MOOT para las nacidas-LIVE; se mantiene para `CAND-`
   legacy en vuelo). Por eso **el consumidor NO maneja ninguna clave estable**:
   pasás el id que viste, el server hace el resto.
   **Por qué NO el `dedup_key`** (hallazgo de Hackaton, 3 lecturas del código): el
   `dedup_key` **no se persiste en la ficha ni lo sirve `saber_ficha`** (es el
   kebab que se pasa al capturar, nada más) — no hay de dónde leerlo. El único id
   estable real es el `content_key`, y **vive en el server**: por eso el contrato
   es "pasá el `entry_id`, el server coalesce", no "anclá vos a una clave estable".
   Campos del evento:
   - `run_ledger_ref` = el **slug-id kebab de ESTA corrida** (el campo `id:` de la
     fila, ej. `2026-07-24-saber-fase2-promocion-inmediata`) — string idéntico
     byte a byte al que el consumo aguas abajo lee. **NO la ruta de la fila, NO la
     cabecera humana del ledger.** (Este campo SÍ es estable y usable hoy.)
   - `event_id` = `cita:<corrida-slug>:<entry_id>` — clave de idempotencia
     determinista (**un solo id-de-corrida en todo el loop**; un retry no duplica).
   - `sesion` = el **session_id del cliente MCP** — **NO el slug de la corrida**:
     las consultas (`saber_buscar`) ocurren ANTES de que la corrida tenga id, así
     que el `sesion` debe ser estable TODA la sesión. **Mismo string en la consulta
     y en la cita** (el server lo guarda verbatim; `saber_consultas(sesion)` lee por
     ese string).
   - **Ref para auditar en `CITAS_SABER:` = el `entry_id`.** `saber_ficha` **NO
     expone** el `content_key`: el server resuelve el `entry_id`→`content_key`
     (`content_key_for`) internamente antes de registrar — el consumidor **siempre
     pasa el `entry_id`** y nunca maneja clave estable. Registrás el `entry_id` en
     `CITAS_SABER:`.
   **Ejemplo de evento** (contrato confirmado vivo, corrida server de Hackaton CLOSED):
   `saber_telemetria(eventos=[{event_id: "cita:<slug>:<entry_id>", entry_id: "<GAP-nnn>",
   run_ledger_ref: "<slug-kebab>"}], sesion="<mcp-session-id>")`.
   Cuenta como ALEGADO e HISTORIAL, no como uso.

   > **DOCTRINA DURA — la FORMA del `run_ledger_ref` (causa raíz probable de las
   > citas en 0).** El ref DEBE matchear
   > `^[A-Za-z0-9][A-Za-z0-9._/#:@-]{0,160}$` — **NO espacios, NO em-dash (—), NO
   > paréntesis.** El servidor **no coteja** el ref contra nada: sólo valida su
   > FORMA. Un ref con la cabecera humana del ledger (que trae espacios, em-dash o
   > paréntesis) **rebota con `InputError` SILENCIOSO** — la cita se pierde sin
   > avisar. Es la causa raíz probable de que las citas causales estén en 0. El
   > slug-id kebab es regex-safe por construcción (PK, ADR 0016). Fuente:
   > `lucky-tool-saber/saber/telemetry.py:28` (`_REF_RE`).
4. **Reportá** qué citas quedaron alegadas — los `entry_id` citados para el campo
   `CITAS_SABER:` del cierre (crisol §4 paso 8) — o `N/A (no se consultó saber en
   esta corrida)` explícito. La **PRESENCIA** del campo la exige `registros-lint` en
   corridas nuevas (CLOSED con `creado >= 2026-07-24`; no-retroactivo, `N/A` vale —
   es presencia, no contenido).
5. **Sin MCP** → fail-open: dejá las citas anotadas vía el flujo /idea (`saber:
   cita causal pendiente <entry_id> · ref <corrida-slug>`) para reportarlas desde
   una sesión con el connector. Nunca se pierden, nunca bloquean el cierre.

---

## Reglas duras

- **El juicio humano vive en la CURADURÍA** (ADR 0028): cada **fusión** y cada
  **poda** exige confirmación de ESE ítem — **jamás batch, jamás auto**; un sí no
  es un sí al lote. El endoso ficha-por-ficha se **MOVIÓ** del gate pre-LIVE a la
  curaduría posterior + el override (`endosar.py`): no murió, cambió de momento.
- **Jamás fingir una capacidad que el MCP no da.** La fusión y la poda las
  **PROPONE** `saber_destilar_proponer` (read-only); el acto de fusionar o
  archivar lo confirma el humano y lo aplica el override — el MCP nunca
  auto-fusiona ni auto-poda. Enumerar ramas legacy no tiene tool: la bandeja es el
  parking local.
- **El espejo local de `bitacora` NO se toca** (`INDEX.md`/`entries/`/
  `SENALES.md` son READ-ONLY generados desde el saber): una edición a mano se
  pierde en la próxima regeneración.
- **`docs/IDEAS.md` solo por append** — se agregan líneas (capturada, citada,
  pendiente); jamás se edita ni se borra una línea vieja.
- **Cero secretos en fichas y reportes** (leak): nombres de variable, nunca
  valores; `<host>`/`<REDACTED>`; rutas relativas, nunca absolutas con usuario.
- **`NADA COSECHABLE` se respeta:** no se re-spawnea al destilador para insistir;
  una cosecha honestamente vacía es un resultado válido.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.11.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo
(`raw.githubusercontent.com/mlandolfi90/lucky-skills/<tag>/plugins/lucky/skills/saber/SKILL.md`)
e informar al humano. **Caso de skill nueva:** si el tag remoto mayor existe pero
NO incluye `saber/` (la skill nació en este bump), tratar como sin-red — seguir
esta copia y registrar `LEY: <tag> (local, skill nueva sin verificar)`. Sin red:
seguir esta copia.

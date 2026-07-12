---
name: bitacora
description: >-
  La Bitácora — catálogo de patrones experienciales "cuando ves SÍNTOMA X →
  hacé ACCIÓN Y", indexado por síntoma para sortear gaps/greps/drifts sin
  re-derivar. Disparar cuando el agente o el usuario: re-deriva algo que ya se
  resolvió, grepea sin mapa o se pierde navegando ("¿dónde vive X?"), detecta
  que doc y código divergen, ve un test en verde que igual rompió (falso-verde),
  o pregunta "¿esto ya pasó?", "¿cómo se sorteaba esto?". "/bitacora" sin
  argumentos = mostrar el INDEX. NO disparar para implementar la solución (eso es
  trabajo normal), ni para capturar ideas a futuro (eso es /idea). Consultá →
  devolvé SOLO la línea de acción → volvé al trabajo.
allowed-tools: Read, Grep, Bash
---

# La Bitácora — "esto ya pasó: así se sortea"

La brújula dice **dónde estás**; el Crisol dice **si está bien hacerlo**; la
Bitácora dice **cómo se sortea lo que ya pasó**. Complementa al Crisol, no lo
reemplaza. **Principio rector: la brújula LEE, el Crisol ESCRIBE.**

**Ejes:** indexada por SÍNTOMA (no por tema) · compacta (≤1 pantalla el INDEX) ·
viva (se pudre si no se valida → reloj `validated_on`) · *compass, not
encyclopedia* (devolvé la acción, jamás vuelques el archivo entero).

## Consultar (AL PLANEAR / solucionar — pull, on-demand)

1. **Cuándo:** justo ANTES de planear o resolver algo (la CONSULTA no es al
   arranque; lo que sí llega al arranque es el **push** del top del INDEX — ver
   §Push — que no reemplaza esta consulta dirigida). **Grep del
   INDEX por el SÍNTOMA de la tarea** — las palabras de lo que vas a tocar:
   `grep -i "<lo que vas a tocar>" INDEX.md` (relativo a esta skill). **El síntoma ES el filtro;
   no hay "dominios".** El INDEX está ordenado por `usos` — lo que más duele, arriba.
2. **Match → abrí la entrada lazy:** leé SOLO `entries/<ID>.md` que matcheó. No
   leas todas; no vuelques el INDEX completo al contexto (eso reintroduce el
   context rot que la Bitácora cura).
3. **Devolvé SOLO la línea de ACCIÓN** (+ la ANTI-ACCIÓN, que evita re-derivar el
   camino muerto). Si la entrada está `STALE` → mostrala con la bandera
   **"⚠ verificar antes de confiar"**, no como verdad vigente.
4. **Sin match → seguí normal.** La Bitácora cubre lo *conocido-recurrente*; lo
   *nuevo* es Crisol/spike. Nunca inventes una entrada para responder.

`/bitacora` sin argumentos = mostrar el INDEX tal cual.

## El saber central es la fuente de verdad (este INDEX es un ESPEJO)

El **saber centralizado** del stack (repo privado `lucky-saber`, servido por el MCP
`lucky-tool-saber` vía litellm) es la **ÚNICA fuente de verdad** de la bitácora. Los
`INDEX.md` / `entries/` / `SENALES.md` de esta skill son un **ESPEJO read-only regenerado
desde el saber** (`scripts/bitacora-espejo.py`, des-scopeado a 7 columnas) — **NO se autoran a
mano** (una edición a mano se PIERDE en la próxima regeneración). La flota SIN el MCP consume este
espejo embebido en la LEY (grep del INDEX + el push hook del arranque); las sesiones CON el MCP
prefieren el saber vivo.

- **Consultar con el MCP** (si están las tools `mcp__lucky-mcp__lucky_saber-*`): preferí
  `saber_buscar(<síntoma>, scopes=[...])` al grep local — trae el catálogo VIVO y centralizado,
  filtrado por scope (`global` + el stack del repo). `saber_ficha(<ID>)` para el cuerpo.
- **Consultar sin el MCP** (offline): grep del INDEX espejado de esta skill (§Consultar) — el
  espejo es el fallback FIEL, no una fuente independiente.
- **El espejo se refresca** cuando el saber cambia: el operador corre `scripts/bitacora-espejo.py`
  y forja un release; la flota lo recibe por ley-live. El saber y el espejo convergen por esa vía.

## Capturar (el costo agudo ES evidencia) — SIEMPRE al saber, NUNCA al espejo

**Principio (2026-07-10): el costo agudo de UNA sola sesión ES evidencia
suficiente.** Un incidente que quemó horas/iteraciones y dejó postmortem no es
una "sospecha" que deba repetirse para valer: ya pagó su entrada. El umbral
`≥2 sesiones` es EXCLUSIVO del carril SENALES (sospechas crónicas, Heinrich).

**Disparador OBJETIVO** (no "cuando parezca"): la sesión/corrida tuvo un
**gap que costó >30min**, un **grep que re-derivó algo ya sabido**, un **drift
hallado**, o **costo agudo intra-sesión** (postmortem escrito · ≥K iteraciones
fallidas sobre el mismo síntoma). Entonces — la captura va al **SABER**, JAMÁS
al espejo local (que es READ-ONLY, generado):

1. **Con el MCP:** destilá el patrón (un síntoma observable = una acción) y
   proponelo con `saber_proponer_ficha(sintoma, tipo, causa_raiz, accion,
   anti_accion, prevencion, scope=…)`. Nace `CANDIDATE` en una rama `mcp-inbox/*`
   — **nunca toca main**; el humano la mergea (`saber_mergear` o por PR). Sospecha
   débil, sin evidencia dura → `saber_senal(sospecha, contexto)`.
2. **Sin el MCP (offline):** anotá el patrón a **`/idea`** (parking local) como
   "síntoma → acción" y proponelo al saber después, desde una sesión con el
   connector. **El espejo local NO se edita a mano.**
3. **`scope`:** `global` (guardrail transversal) · `stack:<tec>` · `repo:<nombre>`
   — lo afina el humano al endosar.
4. **Propiedad humana sobre la promoción (anti documentation-theater):** el agente
   PROPONE `CANDIDATE`; **el humano** mergea a main (entra al saber) y luego lo
   promueve a `LIVE` como acto deliberado. El LLM destila, el humano decide qué es
   verdad; el MCP nunca escribe `usos`/`estado`/`scope`.

## Push (hooks del plugin — ADR 0010, absorbido de ECC continuous-learning-v2)

Dos hooks deterministas, **fail-open total** (jamás rompen una sesión de la
flota), ambos con off-switch por env:

- **`hooks/bitacora-push.sh`** (SessionStart): inyecta el **top-N de filas LIVE**
  del INDEX (síntoma → acción → ID) como contexto al arrancar — modelo push: el
  patrón llega ANTES del tropiezo. Respeta la regla del INDEX ("no volcar el
  archivo entero"): cap `BITACORA_PUSH_MAX` (default 6) + presupuesto duro
  `BITACORA_PUSH_MAX_CHARS` (default 2000, recorte marcado). Solo en `startup`
  (resume/clear/compact no re-inyectan). CANDIDATE/STALE jamás se inyectan.
  Apagar: `BITACORA_PUSH=off`.
  **Timbre de juicio (⚖ JUICIO PENDIENTE, enmienda ADR 0010):** el mismo push
  cuenta lo que espera decisión HUMANA — señales con `visto ≥ 2` en el log del
  observador y entradas CANDIDATE del INDEX — y le ordena al agente avisarle
  al humano en su primera respuesta. Solo suena si hay algo (cero ruido); va
  antes de los patrones (sobrevive al recorte). El conteo es determinista;
  el juicio sigue siendo tuyo.
- **`hooks/bitacora-observar.sh`** (SessionEnd): barre el transcript con **grep
  determinista de señales conocidas** (bloqueos de gate, suites rojas,
  integridad, ley diferida, falso-verde) y acumula SOLO `etiqueta + conteo` en un
  log LOCAL por máquina (rotación dura 400 líneas; cero contenido, cero rutas
  completas — zero-leak por construcción). El log es **evidencia cruda para el
  humano** (`--resumen` lo agrega): alimenta los contadores de `SENALES.md` a
  mano; NADA entra al INDEX por esta vía (la regla "sin evidencia real, NO
  entra" y el endoso humano quedan intactos). Apagar: `BITACORA_OBSERVAR=off`.

**Puente log↔SENALES (enmienda 2, absorbido de la escalera de frecuencia de
ECC):** el timbre además detecta etiquetas del log con **≥2 sesiones acumuladas
que no tienen señal formal en SENALES.md** y propone la cosecha. Donde ECC
auto-promueve al cruzar un umbral de confianza, acá la escalera TERMINA en el
endoso — el conteo sugiere, el humano formaliza.

**Timbre de intensidad (enmienda 3 — "el costo agudo ES evidencia"):** el
timbre también detecta etiquetas con `x ≥ BITACORA_INTENSIDAD_UMBRAL`
(default 10) en UNA sola sesión del log y propone la **cosecha de INTENSIDAD**
(proponer una ficha CANDIDATE al saber si hubo aprendizaje real). Sin este timbre, la
intensidad repetiría el gap original: acumular sin que nadie avise.

Tests: `tests/test-push.sh` · `tests/test-observar.sh`.

## Cosechar (`/bitacora cosechar` — on-demand, SOLO lo invoca el operador)

La pieza LLM del observer de ECC, vuelta doctrinal: nunca corre sola, nunca
escribe sin endoso. Cuando el operador la pide:

Dos modos, cada uno con su DESTINO — no confundirlos:

**Modo FRECUENCIA (→ `saber_senal`, sospechas crónicas):**

1. Leé el agregado del log: `bash hooks/bitacora-observar.sh --resumen`.
2. Por cada etiqueta con `≥2 sesiones` SIN señal formal, **redactá un BORRADOR de
   señal** (síntoma en prosa observable · `visto: N` del conteo real · contexto de
   1 línea) y, endosado, proponelo al saber con `saber_senal(sospecha, contexto)`
   (offline → `/idea`). Si la señal ya existe en el saber: reportá "acumuló N
   avistamientos" para que el humano la suba al endosar.

**Modo INTENSIDAD (→ `saber_proponer_ficha`, costo agudo de UNA sesión):**

3. Por cada etiqueta con `x ≥ umbral` en UNA sola sesión del log
   (`BITACORA_INTENSIDAD_UMBRAL`, default 10), ofrecé **proponer una ficha
   CANDIDATE al saber** con `saber_proponer_ficha(...)` (offline → `/idea`).
   **El log solo prueba QUE dolió, no QUÉ dolió:** el contenido (síntoma, causa
   raíz, acción que FUNCIONÓ) sale del postmortem/transcript o de lo que el humano
   cuente — si no hay material para el QUÉ, declaralo y NO inventes la ficha.

**Reglas de AMBOS modos:**

4. **Presentá los borradores al humano** — uno por uno, con el conteo como
   evidencia. Endosado → se PROPONE al saber (`saber_senal` / `saber_proponer_ficha`;
   el humano mergea); refutado → se descarta anotando el porqué en la respuesta.
   **JAMÁS edites el espejo local a mano; JAMÁS propongas nada no endosado.**
5. Meta-ruido (CRÍTICO, doble en intensidad): si la sesión cosechada EDITÓ la
   bitácora/tests/gates (las palabras de las señales aparecen por TRABAJO, no
   por incidente), declaralo y descontá con criterio — el conteo crudo no
   distingue: una sesión que forjó la bitácora marca ×35 sin que nada haya
   dolido; una de debug real marca ×35 porque dolió. El contexto decide.

## Mantener (mecánico, no por disciplina)

- **Espejo:** el catálogo VIVE en el saber; acá se REGENERA el espejo con
  `python scripts/bitacora-espejo.py` (des-scopea desde `lucky-saber`) y se forja
  un release para propagarlo a la flota. Poda, ascenso y la promoción CANDIDATE→LIVE
  ocurren en el saber (el espejo los refleja); las verificaciones de abajo son
  read-only sobre el espejo generado.
- **STALE:** `bash scripts/bitacora-stale.sh` marca toda entrada con
  `validated_on` > 90 días o sin `validated_on`. Read-only: reporta, no borra.
  Candidato a correr desde el heartbeat (`crisol-pulso`) o el CI.
- **Coherencia (lint):** `bash scripts/bitacora-lint.sh` verifica que el INDEX
  no MIENTA sobre las entradas: bijección INDEX↔`entries/`, `estado`/`usos`/
  `validated_on` espejados, campos obligatorios, ≤35 líneas, orden por `usos`.
  **Fail-closed en la FORJA** (corre tras el leak-scan y aborta el release si el
  catálogo está incoherente); el gate de commits sigue SIN bloquear por la
  Bitácora. Tests: `tests/test-lint.sh`.
- **Poda por tope (~40 entradas vivas):** superado el tope, la de menor `usos` +
  más vieja se archiva con su razón (*el por-qué-se-jubiló también es
  conocimiento*: evita re-proponer lo descartado).
- **Poda de SEÑALES:** señal refutada, o >90 días sin avistamiento nuevo, se
  borra de `SENALES.md` con una línea de por qué (mismo principio que el
  archivo de podas: lo descartado también es conocimiento).
- **Ascenso (válvula anti-pantano):** patrón con `usos ≥ 3` o explicado en >2
  RETROs → asciende y se reemplaza por un puntero: → **ADR** (decisión), →
  **skill** (proceso que el agente ejecuta), → **regla del gate** (invariante
  determinista). La Bitácora NO acumula: recicla hacia arriba. El éxito se mide en
  entradas RETIRADAS, no acumuladas.

## Reglas duras

- **El espejo local es READ-ONLY.** `INDEX.md`/`entries/`/`SENALES.md` se REGENERAN
  desde el saber (`scripts/bitacora-espejo.py`); una edición a mano se pierde en la
  próxima regeneración. Toda captura va al saber (`saber_proponer_ficha`/`saber_senal`)
  o, offline, a `/idea`. El saber es la fuente de verdad; esta skill LEE + refleja.
- **Sin evidencia real, NO entra.** El catálogo guarda solo lo CONFIRMADO por el
  uso: una entrada nace de una corrida con dolor real y evidencia verificable
  (sha/ledger/postmortem). La previsión/teoría va a `/idea` (parking) hasta que la
  realidad la valide. `CANDIDATE` es una **transición corta** (evidencia real
  esperando el endoso humano), no un depósito de teoría — regla del operador,
  2026-07-02: "¿de qué sirve guardar algo que no está confirmado que funcione?".
- **Indexá por SÍNTOMA observable, no por tema.** Si no podés escribir el síntoma
  como algo que un agente OBSERVA literalmente, no es un patrón → va a `/idea`.
- **Señales débiles (near-miss log, `SENALES.md`):** la SOSPECHA de patrón sin
  evidencia no entra al INDEX ni se tira — se acumula en `SENALES.md` con
  contador (`visto: N` + fecha + contexto de 1 línea). La frecuencia del
  casi-incidente predice el incidente (hiyari-hatto / weak signals / ley de
  Heinrich). `visto ≥ 2` → investigación ACTIVA en la próxima corrida que la
  roce: valida (→ CANDIDATE con `validated_on`) o refuta (→ se borra con el
  porqué). SENALES **jamás se consulta para decidir una acción** — eso es
  exclusivo del INDEX; cero secretos, igual que el catálogo. Regla del
  operador, 2026-07-03.
- **Cero secretos (invariante #1):** nombres de variable, nunca valores; rutas
  relativas, nunca absolutas; sin IPs/dominios/tokens. Lo cubre `leak-scan.sh`.
- **Máx ~20-35 líneas por entrada.** Más que eso = es un ADR o una skill, movelo.
- **El gate NO bloquea por la Bitácora** (sería anti-jidoka): el Crisol avisa, no
  exige. Es `.md` → exento del gate; la dureza la dan el origen (Crisol) + STALE.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.41.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

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
allowed-tools: Read, Grep, Bash, Write, Edit
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

## Capturar (Destilación — el costo agudo ES evidencia)

**Principio (2026-07-10): el costo agudo de UNA sola sesión ES evidencia
suficiente para el INDEX.** Un incidente completo que quemó horas/iteraciones
y dejó postmortem no es una "sospecha" que deba repetirse para valer: ya pagó
su entrada. El umbral `≥2 sesiones` es EXCLUSIVO del carril SENALES (sospechas
crónicas, Heinrich); jamás se le exige a un confirmado-por-dolor. Dos rampas
al INDEX:

- **Cierre del Crisol** (§4 paso 8) — la rampa clásica: no se escriben
  entradas sueltas a mano; nacen al cerrar la corrida.
- **Cosecha por INTENSIDAD** (§Cosechar, modo intensidad) — la rampa para
  sesiones hot-iteration SIN Crisol: el timbre detecta la intensidad, el
  humano pide la cosecha, el agente destila CANDIDATE.

**Disparador OBJETIVO** (no "cuando parezca"): la sesión/corrida tuvo un
**gap que costó >30min**, un **grep que re-derivó algo ya sabido**, un **drift
hallado**, o **costo agudo intra-sesión** (etiqueta del observador con
`x ≥ umbral` en UNA sesión · ≥K iteraciones fallidas sobre el mismo síntoma ·
postmortem escrito). Entonces:

1. **Destilá UNA entrada** con `templates/entrada.md`. Una entrada = un síntoma =
   una acción. El título ES el síntoma observable, con tag `[TIPO-NNN]`.
2. **Dedup primero:** `grep` del síntoma en `INDEX.md`. Si ya existe → NO crees
   otra: incrementá `usos` y refrescá `validated_on`.
3. **`validated_on` OBLIGATORIO** (`branch · fecha · commit`). Sin él, nace STALE.
4. **Propiedad humana sobre la promoción (anti documentation-theater):** el agente
   destila con `estado: CANDIDATE`; **el humano** promueve a `LIVE` como acto
   deliberado de cierre. El LLM destila, el humano decide qué es verdad.
5. Agregá la fila al `INDEX.md` y listá la entrada en el resumen de cierre del
   Crisol (junto al Parking de IDEAS.md).

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
(destilar a INDEX-CANDIDATE si hubo aprendizaje real). Sin este timbre, la
intensidad repetiría el gap original: acumular sin que nadie avise.

Tests: `tests/test-push.sh` · `tests/test-observar.sh`.

## Cosechar (`/bitacora cosechar` — on-demand, SOLO lo invoca el operador)

La pieza LLM del observer de ECC, vuelta doctrinal: nunca corre sola, nunca
escribe sin endoso. Cuando el operador la pide:

Dos modos, cada uno con su DESTINO — no confundirlos:

**Modo FRECUENCIA (→ SENALES, sospechas crónicas):**

1. Leé el agregado del log: `bash hooks/bitacora-observar.sh --resumen`.
2. Por cada etiqueta con `≥2 sesiones` SIN señal formal en `SENALES.md`,
   **borrá un BORRADOR de señal** (formato de la tabla de SENALES: señal en
   prosa observable · `visto: N` heredado del conteo real del log · fecha ·
   contexto de 1 línea). Si tenés contexto de las sesiones donde sonó, usalo;
   si no, el borrador lo declara ("contexto por confirmar").
3. Etiquetas que ya tienen señal formal: solo reportá "la señal X acumuló
   N avistamientos nuevos" para que el humano actualice `visto:` si endosa.

**Modo INTENSIDAD (→ INDEX-CANDIDATE, costo agudo de UNA sesión):**

4. Por cada etiqueta con `x ≥ umbral` en UNA sola línea/sesión del log
   (`BITACORA_INTENSIDAD_UMBRAL`, default 10), ofrecé **destilar una entrada
   CANDIDATE del INDEX** con `templates/entrada.md` — NO una señal.
   **El log solo prueba QUE dolió, no QUÉ dolió:** el contenido (síntoma
   observable, causa raíz, acción que FUNCIONÓ) sale del postmortem, del
   transcript o de lo que el humano cuente — si no hay material para el QUÉ,
   declaralo y NO inventes la entrada. `validated_on` = la sesión del
   incidente; la evidencia es el COSTO (conteo + postmortem).

**Reglas de AMBOS modos:**

5. **Presentá los borradores al humano** — uno por uno, con el conteo como
   evidencia. Endosado → se escribe (SENALES o INDEX+entrada según el modo);
   refutado → se descarta anotando el porqué en la respuesta (no en el
   archivo). JAMÁS escribas nada no endosado.
6. Meta-ruido (CRÍTICO, doble en intensidad): si la sesión cosechada EDITÓ la
   bitácora/tests/gates (las palabras de las señales aparecen por TRABAJO, no
   por incidente), declaralo y descontá con criterio — el conteo crudo no
   distingue: una sesión que forjó la bitácora marca ×35 sin que nada haya
   dolido; una de debug real marca ×35 porque dolió. El contexto decide.

## Mantener (mecánico, no por disciplina)

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
`v1.35.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

---
id: adr:0028
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-24
supersede: null
superseded_by: null
refs: [corrida:2026-07-24-saber-fase2-promocion-inmediata, adr:0023, adr:0027, adr:0015, adr:0024]
---

# 0028 — Saber Fase 2: promoción inmediata; el juicio humano se MUEVE a la curaduría

## Contexto

Hasta hoy el saber tenía una compuerta pre-LIVE: la captura nacía `CANDIDATE`
en una rama `mcp-inbox/*`, y **solo un acto humano ficha-por-ficha** la mergeaba
y la promovía a `LIVE` (ADR 0023 §4, "un sí no es un sí al lote"). La doctrina
que lo justificaba era doble: **"contar ≠ ungir"** (una cita alegada informa
pero no promueve — ADR 0027 §2) y **"sin evidencia real NO entra"** (el catálogo
guarda solo lo confirmado por el uso — ADR 0015, doctrina de la bitácora). El
juicio humano vivía ANTES de que la ficha se sirviera.

Dos cosas movieron el modelo el 2026-07-24:

1. **El operador endosó directo el modelo b** ("dale gooo"), tras el surface
   explícito de que el cambio DEROGA su invariante más enfático (endoso humano
   por-ficha pre-LIVE). No se ejecutó por relay: lo autorizó él mismo,
   entendiendo la tensión. El norte que lo hace coherente con su ley: **el
   principio "el humano decide qué es verdad" NO muere — se MUEVE** de
   gate-pre-LIVE a curaduría-posterior. Cambia el MOMENTO del juicio, no su
   existencia.

2. **RAG midió el costo del gate** (`saber_metricas`, 2026-07-24): de ~50 fichas,
   las **consultas** fluyen (DRIFT-004 con 16, DRIFT-001 con 13) pero las
   **citas causales** están casi todas en 0. La compuerta pre-LIVE no producía
   la evidencia que ella misma exigía: fichas útiles se quedaban `CANDIDATE`
   porque nadie corría el ritual de promoción. El gate no protegía calidad;
   frenaba el aprendizaje.

El server del saber (lane Hackaton, `lucky-tool-saber`) cerró su corrida y pineó
el contrato (commit `77f6138`, e2e verde): la captura ahora **sirve LIVE en
main** por contenido, `CANDIDATE` se elimina para fichas, y dos tools nuevas
(`saber_historial`, `saber_destilar_proponer`) habilitan la curaduría. Este ADR
consume ese contrato del lado de las skills.

## Decisión

1. **Captura → LIVE directo.** `saber_proponer_ficha(...)` conserva el nombre y
   estrena semántica: ya no va a inbox-`CANDIDATE`, **captura y sirve LIVE en
   main** (vía `capturar_directo`, que reusa la máquina de `mergear`). ACK
   `capturada`; id de captura directa = `CAP-<content_key>`. El `dedup_key` queda
   **vestigial** (la idempotencia es por contenido, `content_key`). **El estado
   `CANDIDATE` se ELIMINA para las fichas.**

2. **La cita causal es HISTORIAL, no gate.** `/saber citar` sigue registrando la
   cita alegada (mecánica congelada, ADR 0027), pero su ROL cambia: alimenta
   `saber_historial(entry_id)` — el registro de cómo/cuándo una ficha funcionó
   (ts · veredicto · sesión · run_ledger_ref · contexto). 0 citas = `SERVIDA SIN
   PROBAR`. Ya no es "asesor de la promoción" porque la promoción es inmediata.

3. **El juicio humano se MUEVE a la curaduría (`/saber destilar`).** El acto
   deliberado del humano deja de ser el endoso ficha-por-ficha pre-LIVE y pasa a
   ser el **ritual de curaduría batch, posterior**: consolidar el catálogo LIVE
   con sus historiales, **fusionar cuasi-duplicados** (el humano confirma cada
   fusión) y **PROPONER la poda** de la evidencia-cero tras una ventana ~30d
   (reversible = archivar; el humano confirma). El momento del juicio se corre,
   no se elimina.

**Derogaciones POR PUNTO** (los registros son inmutables — ADR 0016 §4: los ADR
viejos quedan `estado: ACEPTADA` byte-intactos; 0028 los linkea por `refs:` y
deroga cada punto acá, JAMÁS por `supersede:` de ADR entero, que los leería
muertos enteros y borraría lo que de cada uno se CONSERVA):

- **"Contar ≠ ungir" / la cita informa pero no promueve** — ADR 0027 §2 y
  `saber/SKILL.md:150,203`. **Derogado como gate:** ya no hay promoción que la
  cita deba abstenerse de mover; la cita es historial. (Se CONSERVA la mecánica
  de `/saber citar` — punto siguiente.)
- **"CANDIDATE→LIVE solo por acto humano" / "endoso POR FICHA, jamás batch"
  pre-LIVE** — ADR 0023 §4 y `saber/SKILL.md:227,96`. **Derogado como puerta de
  entrada:** no hay transición `CANDIDATE→LIVE` que endosar; la captura entra
  LIVE directo. El endoso ficha-por-ficha **sobrevive movido**: rige la
  confirmación de CADA fusión en la curaduría y CADA poda (sigue prohibido el
  batch en el juicio posterior).
- **"Sin evidencia real NO entra" como gate pre-LIVE** — ADR 0015 y la doctrina
  de bitácora (`bitacora/SKILL.md:215`). **Derogado como compuerta de entrada:**
  la ficha fresca entra `SERVIDA SIN PROBAR`. La exigencia de evidencia no
  desaparece: se convierte en **poda de salida** (la evidencia-cero se propone
  para archivar), no en veto de entrada.

**CONSERVADO (intacto o movido, jamás eliminado):**

- **"El humano decide qué es verdad"** — `saber/SKILL.md:168`, el ancla nuclear.
  Se MUEVE al momento de la curaduría (fusión + poda con confirmación humana), no
  se toca su principio.
- **La mecánica de `/saber citar`** — ADR 0027 congelada: pasás el `entry_id`, el
  server resuelve a `content_key` y coalesce el rename; el `run_ledger_ref` es el
  slug-id kebab de la corrida (regex-safe, sin espacios/em-dash/paréntesis, o
  rebota con `InputError` silencioso). Solo cambia su ROL (historial).
- **El agente `destilador`** — sigue CAPTURADOR read-only (ADR 0023, sin
  Write/Edit); lo único que cambia es aguas abajo (sus borradores van a LIVE
  directo vía `saber_proponer_ficha`, no a `mcp-inbox`). Su gatillo se renombra a
  `/saber capturar` para no colisionar con `/saber destilar`, que ahora es la
  curaduría.

## Consecuencias

- **`saber/SKILL.md` se reescribe** al modelo nuevo: `/saber` reporta la ventana
  de gracia evidencia-cero (no "CANDIDATE esperando promoción"); `/saber revisar`
  pasa a **override excepcional** (`endosar.py` / `mergear` para ideas·señales·
  legacy), no puerta de entrada; `/saber promover` se deroga como paso de ciclo
  (la promoción es inmediata por captura); `/saber podar` se EXTIENDE
  (`saber_destilar_proponer(modo='poda', dias_poda=30)` propone read-only, el
  humano confirma, reversible = archivar — única garganta de poda); `/saber
  destilar` es el ritual nuevo de curaduría; `/saber capturar` es el renombre de
  la captura-al-cierre. `/saber citar` se conserva con rol de historial.

- **El trade de seguridad, HONESTO.** La captura fresca se sirve **SIN PROBAR**:
  se pierde una de las dos capas de evidencia que daba el endoso pre-LIVE. El
  server lo modela como un **2-latch** (ADR 0008 del lane Hackaton,
  `lucky-tool-saber` — NO el ADR 0008 local): el colchón que reemplaza al gate es
  la **señal de citas** (`saber_historial` marca lo `SERVIDA SIN PROBAR`) + la
  **poda de evidencia-cero** (sale lo que a ~30d no juntó ni una cita ni un uso).
  La revisión adversarial de Hackaton lo dio **SAFE**: ningún vector corrompe una
  guía LIVE existente sin gate (la captura fresca coexiste, no sobreescribe). Se
  documenta el trade, no se esconde: es el precio explícito de mover el juicio.

- **La poda es propone-humano-confirma, jamás auto-poda.**
  `saber_destilar_proponer` es **READ-ONLY**: computa los candidatos evidencia-
  cero (0 citas + `usos=0` + edad ≥ ~30d) y los PROPONE; el acto de archivar lo
  confirma el humano. Ninguna tool auto-poda. Reversible por construcción
  (archivar, no borrar: el por-qué-se-jubiló también es conocimiento).

- **La fusión tiene regla horneada (insumo de RAG).** El discriminante de
  duplicación es **CAUSA-RAÍZ + ACCIÓN**, jamás el síntoma o el vocabulario (lo
  que "suena" parecido suele ser complementario, vinculado por `refs:` — 12
  escépticos opus dieron 0/12 cuasi-dups aparentes que debieran fusionarse). El
  **default ante duda es NO fusionar** (la fusión es irreversible y destruye
  conocimiento). El comando **PROPONE, nunca fusiona solo**: el humano confirma
  cada fusión, y la UX muestra causa+acción de cada par para que juzgue por lo que
  importa, no por cómo suena. `veredicto_sugerido` del server es SIEMPRE
  `REVISAR`.

- **`endosar.py` (lucky-saber, fuera del MCP) COEXISTE como override manual.** El
  portón de endoso no se borra: sigue vivo como override humano para
  ideas/señales/legacy y para corregir el catálogo a mano.

- **`saber_mergear`/`saber_refs`/`saber_metricas` quedan byte-idénticos**;
  `mergear` sirve solo a ideas/señales + override humano/legacy. Las `CANDIDATE`
  legacy en vuelo coalescen por `content_key` al flipear (el coalesce del rename
  queda MOOT para las nacidas-LIVE).

- **Cadencia de la curaduría:** barata, sugerida al cierre de corrida o por umbral
  acumulado; el núcleo de valor es la fusión de cuasi-dups (los exactos ya los
  dedup el `content_key` en captura).

- **Considerado y descartado a propósito:**
  - **Auto-poda** al cruzar la ventana — violaría la propiedad humana sobre el
    catálogo; la poda es ALEGADA por la tool, ACTADA por el humano.
  - **Fusión automática por similitud de síntoma** — el síntoma "suena" parecido
    y engaña; el discriminante es causa-raíz+acción y el default es no fusionar.
  - **Un ID de matriz que verifique el CONTENIDO de la cita/curaduría** — daría
    falso FAIL en corridas que legítimamente no consultan saber (mismo jidoka que
    ADR 0027 §4); la señal es de PRESENCIA, no de contenido.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.10.2` (cache local, NO la ley).**

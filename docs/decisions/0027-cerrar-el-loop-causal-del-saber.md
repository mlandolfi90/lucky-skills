---
id: adr:0027
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-24
supersede: null
superseded_by: null
refs: [corrida:2026-07-24-cierre-loop-causal-saber, adr:0023]
---

# 0027 — Cerrar el loop causal del saber

## Contexto

El cierre del Crisol tiene DOS ejes del saber, y hasta hoy solo UNO estaba
cableado:

- **CAPTURA (destilación)** — "¿qué ficha NUEVA nace de esta corrida?" — ya tiene
  enganche: el campo `BITACORA:` se registra SIEMPRE al cerrar (refs de lo
  propuesto o `N/A (sin disparador)`), el `destilador` lo alimenta, y un cierre
  sin el campo se ve en la fila (ADR 0023/0005).
- **REFUERZO (cita causal)** — "¿qué ficha EXISTENTE funcionó de verdad en esta
  corrida?" — **no tiene enganche**. La tool `saber_telemetria` existe y nadie la
  llama. El loop `consulta → refuerzo` no cierra: una ficha se consulta pero
  nunca queda registrado que ayudó, así que su `usos`/citas no crecen y la
  promoción CANDIDATE→LIVE se queda sin la evidencia que la justifica.

La sesión de RAG lo MIDIÓ hoy (2026-07-24) con `saber_metricas`: de ~50 fichas,
las **consultas** fluyen (DRIFT-004/FALSO-VERDE-004 con 16, DRIFT-001 con 13),
pero las **citas causales alegadas** están en 0 salvo DRIFT-001 (2). El contador
existe y alguna vez avanzó; lo que falta es el hábito, y el hábito falta porque
**no hay campo que lo pregunte al cerrar** — exactamente el mismo hueco que la
CAPTURA tenía antes de que `BITACORA:` lo cerrara.

El diagnóstico es simétrico al de ADR 0023: documentar es guardar; aprender es
que el refuerzo vuelva a la ficha para que el sistema sepa cuál merece vivir.

## Decisión

1. **El cierre de corrida registra SIEMPRE el campo `CITAS_SABER:`** — espejo
   exacto de `BITACORA:`. Contiene las citas causales alegadas de las fichas que
   ayudaron de verdad en la corrida, o `N/A (no se consultó saber)` explícito. Un
   cierre sin el campo se ve en la fila (misma visibilidad que la CAPTURA). El eje
   REFUERZO gana así el mismo enganche que ya tenía el eje CAPTURA.

2. **El vehículo es `saber_telemetria`, y cuenta como ALEGADO — NO mueve `usos`.**
   Registrar una cita causal es un *claim* ("esta ficha parece haber funcionado"),
   no una promoción. El `usos` y el ascenso CANDIDATE→LIVE siguen siendo **endoso
   humano por ficha** (ADR 0023 §4, "un sí no es un sí al lote"): la telemetría
   informa la decisión, no la ejecuta.

3. **El cómo lo define `/saber citar`, no este ADR ni el crisol.** El subcomando
   nuevo reúne las fichas que la sesión consultó, las presenta al humano **ficha
   por ficha** para que confirme cuál funcionó (principio de endoso: el LLM no se
   auto-adjudica que la ficha ayudó), y registra las confirmadas con
   `saber_telemetria`. **La cita se registra pasando el `entry_id`; el server
   resuelve la identidad estable** (corregido por la corrida
   `2026-07-24-loop-causal-content-key`, 3 lecturas del código): `saber_telemetria`
   toma el `entry_id` (el id-display `GAP-nnn`/`CAND-xxx`) y el server lo resuelve
   internamente a su clave estable `content_key` (`sha256(síntoma·acción)`,
   recomputable al servir), **coalesciendo las citas a través del rename
   CANDIDATE→LIVE** (la promoción no toca síntoma/acción). El `dedup_key` **NO** es
   el ancla — no se persiste ni lo sirve `saber_ficha`; el consumidor no maneja
   ninguna clave estable, pasa el `entry_id` y el server hace el resto. El
   `run_ledger_ref` es el **slug-id kebab de la corrida** (el campo
   `id:` de la fila, ej. `2026-07-24-cierre-loop-causal-saber`), **NO la ruta ni
   la cabecera humana del ledger**: el server sólo valida la FORMA del ref
   (`^[A-Za-z0-9][A-Za-z0-9._/#:@-]{0,160}$` — sin espacios, em-dash ni
   paréntesis) y un ref malformado **rebota con `InputError` silencioso** (causa
   raíz probable del contador en 0; `lucky-tool-saber/saber/telemetry.py:28`). El
   crisol §4 y el template solo APUNTAN a `/saber citar` — una define, las demás
   referencian (fuente única).

4. **NO se crea un ID de matriz con FAIL de CONTENIDO, PERO sí un lint de
   PRESENCIA no-retroactivo.** Un gate de matriz probabilístico sobre el CONTENIDO
   de la cita daría un **falso FAIL** en corridas que legítimamente no consultan
   saber — eso se descarta. Lo que SÍ se adopta (**pivote** respecto de la paridad
   estricta con `BITACORA:`) es un chequeo de **PRESENCIA** del campo
   `citas_saber:` en `registros-lint.py`: exigido SÓLO en corridas
   `estado: CLOSED` con `creado >= 2026-07-24` (no-retroactivo — no enrojece las
   históricas), y `N/A` cuenta como presente (**presencia, no contenido** → sin
   falso FAIL). El pivote se justifica por la **asimetría captura/refuerzo**
   (citar da crédito a una ficha AJENA — menos gratificante que destilar una
   propia → el hábito necesita más fuerza que la que le bastó a `BITACORA:`) y
   porque la **auto-promoción LEE esta señal** (el conteo de citas informa el
   ascenso; una señal que alimenta una decisión automática merece cinturón +
   tirantes). El diente queda: **cinturón** (campo obligatorio-de-juicio, visible
   en la fila, mismo jidoka que `BITACORA:`) **+ tirantes** (el lint de presencia).
   Si RETROs futuros muestran cierres con `CITAS_SABER:` mentiroso, esa evidencia
   abre SU corrida (disparador kaizen), no un gate de contenido prematuro.

## Consecuencias

- **`saber/SKILL.md` gana el subcomando `/saber citar <refs>`** — gemelo de
  `/saber destilar` en el gatillo del cierre: uno cablea la CAPTURA, el otro el
  REFUERZO. Define el contrato de `saber_telemetria` (event_id idempotente,
  run_ledger_ref, anclaje al id estable) y su fail-open a `/idea` sin MCP.
- **Anchor corregido (corrida `2026-07-24-loop-causal-content-key`; 3 lecturas del
  código por Hackaton+RAG).** El `dedup_key` NO es el ancla: **no se persiste en la
  ficha ni lo sirve `saber_ficha`** (es el kebab que se pasa al PROPONER). El contrato
  correcto y más simple: **`/saber citar` pasa el `entry_id`** (el id-display
  GAP-nnn/CAND-xxx) y **el server lo resuelve a su clave estable `content_key`**
  (`sha256(síntoma·acción)`, recomputable al servir) y **coalesce las citas a través
  del rename CANDIDATE→LIVE** — el consumidor no maneja ninguna clave estable.
- **Deuda de contrato CERRADA (corrida `2026-07-24-loop-causal-pin-final`; la corrida
  server de Hackaton `lucky-tool-saber` CLOSED, deploy live, e2e verde:
  `metrics(GAP-024)=11=metrics(CAND-af1f29893a9a)` — las consultas varadas bajo el id
  muerto coalescieron bajo el promovido).** Shapes finales: (1) `saber_ficha` **NO**
  expone `content_key` — quedó fuera de scope y **no hace falta**: el server resuelve el
  `entry_id`→`content_key` (`content_key_for`) internamente antes de `record_causal`; el
  consumidor **siempre pasa el `entry_id`** y registra ESE en `CITAS_SABER:`. (2) El param
  se llama `sesion` (en `saber_buscar`/`saber_ficha`/`saber_telemetria`), valor = el
  **session_id del cliente MCP**, mismo string en la consulta y en la cita (el server lo
  guarda verbatim; `saber_consultas(sesion)` lee por ese string). `/saber citar` (v2.10.2)
  pinea el ejemplo de evento exacto. RAG probó el mecanismo VIVO bajo v2.10.1: las citas de
  `FALSO-VERDE-004` y `DRIFT-007` pasaron de `citas_causales` 0→1 con este contrato.
- **`crisol/SKILL.md` §4 paso 8** agrega el ESPEJO inmediatamente después del
  bloque de Destilación/BITACORA: el campo `CITAS_SABER:` se registra SIEMPRE, con
  puntero a `/saber citar` para el cómo. El Crisol AVISA, no exige gate.
- **`crisol/templates/run-ledger.md`** lista `CITAS_SABER:` junto a `BITACORA:` en
  la proyección, y agrega `citas_saber:` como clave de frontmatter de la FILA
  (espejo de `bitacora:`).
- **`scripts/registros-lint.py` gana un lint de PRESENCIA no-retroactivo** del
  campo `citas_saber:` (fila `corrida` en `CLOSED` con `creado >= 2026-07-24`;
  `N/A` vale). Es el **tirante** del pivote de la Decisión §4: la CAPTURA/
  `BITACORA:` no lo tiene y fluye igual, pero el REFUERZO necesita más fuerza
  (asimetría + la señal que la auto-promoción lee).
- **Alcance de ESTA corrida = el MECANISMO, no la primera cita.** Se shipea la
  definición en `lucky-skills` (subcomando + campo + template + test estructural).
  La **primera cita causal EN VIVO** y la promoción CANDIDATE→LIVE que la
  telemetría habilite son del **lane saberes** (canal RAG↔Skills Hackaton), NO de
  esta corrida — límite del operador 2026-07-24 ("cuidado con lo de saberes"). El
  campo `CITAS_SABER:` de esta corrida se cierra honesto: mecanismo shipeado acá;
  primera cita en vivo = lane saberes.
- **Considerado y descartado a propósito**:
  - Un ID de matriz `CITAS_SABER` con FAIL de CONTENIDO — daría falso-positivo en
    corridas que no consultan saber; el jidoka lo prohíbe (paralelo exacto a ADR
    0023, "un ID de matriz DESTILACION"). Distinto del **lint de PRESENCIA** del
    §4, que SÍ se adopta: presencia ≠ contenido (`N/A` pasa → sin falso FAIL).
  - Que `/saber citar` mueva `usos` directo — violaría la propiedad humana sobre
    la promoción; la cita es ALEGADO, no ascenso.
  - Disparar `saber_telemetria` en esta corrida como prueba conductual — fuera de
    alcance por el límite del operador; la prueba RED→GREEN de esta corrida es
    ESTRUCTURAL (test-saber.sh), sin escritura al saber.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.10.1` (cache local, NO la ley).**

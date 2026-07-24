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
   `saber_telemetria`, atándolas al `run_ledger_ref` de la corrida (la fila
   `docs/refactor/_crisol/runs/<id>.md`, el ancla de evidencia que el humano
   cotejará). El crisol §4 y el template solo APUNTAN a `/saber citar` — una
   define, las demás referencian (fuente única).

4. **NO se crea un ID de matriz con FAIL.** Una corrida puede legítimamente no
   consultar ninguna ficha; un gate probabilístico daría un **falso FAIL** en esos
   cierres honestos. El diente es el **campo obligatorio-de-juicio** (presente
   siempre, visible en la fila), no una celda machine-checkable — el mismo jidoka
   que gobierna `BITACORA:` (ADR 0023 §3: sin gate nuevo, sin ID nuevo; la dureza
   es la huella). Si RETROs futuros muestran cierres con `CITAS_SABER:` mentiroso,
   esa evidencia abre SU corrida (disparador kaizen), no un gate prematuro.

## Consecuencias

- **`saber/SKILL.md` gana el subcomando `/saber citar <refs>`** — gemelo de
  `/saber destilar` en el gatillo del cierre: uno cablea la CAPTURA, el otro el
  REFUERZO. Define el contrato de `saber_telemetria` (event_id idempotente,
  entry_id, run_ledger_ref) y su fail-open a `/idea` sin MCP.
- **`crisol/SKILL.md` §4 paso 8** agrega el ESPEJO inmediatamente después del
  bloque de Destilación/BITACORA: el campo `CITAS_SABER:` se registra SIEMPRE, con
  puntero a `/saber citar` para el cómo. El Crisol AVISA, no exige gate.
- **`crisol/templates/run-ledger.md`** lista `CITAS_SABER:` junto a `BITACORA:`
  (opcional-de-formato, NO bloqueante).
- **Alcance de ESTA corrida = el MECANISMO, no la primera cita.** Se shipea la
  definición en `lucky-skills` (subcomando + campo + template + test estructural).
  La **primera cita causal EN VIVO** y la promoción CANDIDATE→LIVE que la
  telemetría habilite son del **lane saberes** (canal RAG↔Skills Hackaton), NO de
  esta corrida — límite del operador 2026-07-24 ("cuidado con lo de saberes"). El
  campo `CITAS_SABER:` de esta corrida se cierra honesto: mecanismo shipeado acá;
  primera cita en vivo = lane saberes.
- **Considerado y descartado a propósito**:
  - Un ID de matriz `CITAS_SABER` con FAIL — daría falso-positivo en corridas que
    no consultan saber; el jidoka lo prohíbe (paralelo exacto a ADR 0023, "un ID
    de matriz DESTILACION").
  - Que `/saber citar` mueva `usos` directo — violaría la propiedad humana sobre
    la promoción; la cita es ALEGADO, no ascenso.
  - Disparar `saber_telemetria` en esta corrida como prueba conductual — fuera de
    alcance por el límite del operador; la prueba RED→GREEN de esta corrida es
    ESTRUCTURAL (test-saber.sh), sin escritura al saber.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.9.0` (cache local, NO la ley).**

---
id: PLAN-cierre-loop-causal-saber
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-07-24
refs: [corrida:2026-07-24-cierre-loop-causal-saber, adr:0023, adr:0025, adr:0027]
nota: "Un solo carril (saber skill + cierre del crisol comparten el contrato del loop causal: partirlo sería el REJECT de 'dos planes, mismo contrato'). El diseño es ESPEJO exacto de un mecanismo probado: la destilación (BITACORA) ya cablea la CAPTURA; esto cablea el REFUERZO con el mismo patrón."
---
# Plan — corrida `2026-07-24-cierre-loop-causal-saber`

Encargo cross-sesión de la sesión de RAG (que midió el problema con `saber_metricas`),
endosado por el operador (goal 'dejar funcional'). Un carril, seis actos.

**El insight:** el cierre del Crisol ya tiene DOS ejes del saber, solo UNO cableado.
CAPTURA (destilación, fichas nuevas) → campo `BITACORA:` registrado SIEMPRE (refs o
`N/A sin disparador`). REFUERZO (cita causal, qué ficha existente funcionó) → sin enganche.
`saber_telemetria` existe y nadie lo llama. Cableamos el espejo.

**A. ADR 0027** (`docs/decisions/0027-cerrar-el-loop-causal-del-saber.md`) — la DECISIÓN:
el cierre de corrida registra SIEMPRE las citas causales (espejo de la destilación/BITACORA
— ADR 0023/0005); el vehículo es `saber_telemetria` (cuenta como ALEGADO — NO mueve `usos`,
eso sigue siendo endoso humano); el subcomando `/saber citar` define el cómo; NO se crea un
ID de matriz con FAIL (una corrida puede legítimamente no consultar ninguna ficha → gate
probabilístico daría falso FAIL; el diente es el campo obligatorio-de-juicio, mismo jidoka
que BITACORA). Formato 0025/0026, estado ACEPTADA.

**B. `saber/SKILL.md` — subcomando nuevo `/saber citar <refs>`** (define el cómo, "una
define, la otra apunta"). Ubicación: junto a `/saber destilar` (ambos son el gatillo del
cierre de corrida). Contenido:
1. Reuní las fichas que ESTA sesión consultó (las que el agente miró con `saber_buscar`/
   `saber_ficha` en el hilo, más las que un verificador canónico aplicó como doctrina —
   ej. el quality-auditor aplica `FALSO-VERDE-004`/`DRIFT-007` al correr REGLA 0).
2. **Por ficha**, presentá al humano cuál PARECE haber funcionado y esperá su confirmación
   (principio de endoso: el humano decide qué es verdad; el LLM no se auto-adjudica que la
   ficha funcionó).
3. Registrá las confirmadas con `saber_telemetria(eventos=[{event_id, entry_id,
   run_ledger_ref, stale?}])` — `run_ledger_ref` = el id de la fila de ESTA corrida
   (`docs/refactor/_crisol/runs/<id>.md`); `event_id` = clave de idempotencia
   (`<corrida-id>:<entry_id>`, un retry no duplica). Cuenta como ALEGADO.
4. Reportá qué citas quedaron alegadas (para el campo `CITAS_SABER:` del cierre) o
   `N/A (no se consultó saber en esta corrida)` explícito.
5. **Sin MCP** → fail-open: dejá las citas anotadas en `/idea` (`saber: cita causal pendiente
   <entry_id> · ref <corrida>`) para reportarlas desde una sesión con el connector. Nunca
   bloquea.

**C. `crisol/SKILL.md` §4 paso 8** — junto al bloque de Destilación/BITACORA, agregar el
ESPEJO: al cerrar, registrá SIEMPRE el campo `CITAS_SABER:` — las citas causales alegadas de
las fichas que ayudaron de verdad (vía `/saber citar`, con el ref de esta corrida), o
`N/A (no se consultó saber)`. Un cierre sin el campo se ve en la fila (misma visibilidad que
BITACORA). El Crisol AVISA, no exige un gate: sin ID de matriz, mismo jidoka que la
destilación. Puntero a `/saber citar` para el cómo (no se re-define acá).

**D. `crisol/templates/run-ledger.md`** — agregar `CITAS_SABER:` a la lista de campos del
bloque de proyección, junto a `BITACORA:` (mismo estilo: opcional-de-formato, NO bloqueante,
crisol §4 paso 8).

**E. Primera cita en vivo — FUERA DE ESTE ALCANCE (límite del operador, 2026-07-24).** El
operador delimitó que "lo de saberes" (escribir al saber, promover CANDIDATE→LIVE) lo maneja
el canal RAG↔Skills Hackaton, NO esta corrida. Por eso esta corrida SÓLO shipea el MECANISMO
en `lucky-skills` (define `/saber citar` y el campo `CITAS_SABER:`); **no dispara
`saber_telemetria` ni toca el repo `lucky-saber`**. La primera cita causal EN VIVO y la
promoción son del lane saberes. El campo `CITAS_SABER:` de ESTA corrida se cierra honesto:
`mecanismo shipeado acá; primera cita en vivo = lane saberes (RAG↔Hackaton)`. La prueba
RED→GREEN de esta corrida es ESTRUCTURAL (acto F), no conductual — sin escritura al saber.

**F. Test estructural** — extender `saber/tests/test-saber.sh` (o assert nuevo): (1) el
subcomando `/saber citar` existe en `saber/SKILL.md` con mención a `saber_telemetria` y
`run_ledger_ref`; (2) `crisol/SKILL.md` §4 nombra `CITAS_SABER`; (3) el template run-ledger
lista `CITAS_SABER`. RED→GREEN: correr ANTES de escribir (los asserts fallan) y DESPUÉS
(verde).

Vehículo: tier completo (toca el contrato del cierre §4 → ADR). Sin re-sello/tag (diferido
al operador). Cero secretos.

## Supuestos del plan (ADR 0025 — tope 5, solo load-bearing)

1. **`saber_telemetria` persiste la cita como ALEGADO y `saber_metricas` la lee** — el
   vehículo funciona end-to-end vía MCP, no es stub. Si fuera falso, la skill queda como
   prosa sin diente hasta reparar el MCP (repo saberes, canal Skills Hackaton). — Fundamento:
   la sesión de RAG lo MIDIÓ hoy (DRIFT-001 tiene 2 citas_causales_alegadas; el contador
   existe y avanzó alguna vez).
2. **El agente conoce, dentro de su sesión, qué fichas consultó** — puede presentarlas sin
   una tool de "consultas de esta sesión" (que no existe). Si fuera falso, se apoya en el
   humano nombrándolas. — Fundamento: no hay tool per-sesión; el agente tiene el hilo y los
   verificadores canónicos nombran las fichas que aplican en su prompt.
3. **Paridad con BITACORA es la dosis correcta: campo obligatorio + visible en la fila, SIN
   gate de lint** — un gate con FAIL daría falso-positivo en corridas que no consultan saber.
   Si fuera falso (RAG o el operador piden diente duro), se agrega chequeo de PRESENCIA del
   campo a `registros-lint.py`. — Fundamento: `BITACORA:` NO está en `registros-lint.py`
   (verificado) y la captura igual fluye; el problema de las citas es que NO hay campo que
   pregunte, no que el campo sea blando.
4. **El `run_ledger_ref` que exige `saber_telemetria` = el id/ruta de la fila de corrida** —
   `docs/refactor/_crisol/runs/<id>.md` es el ancla de evidencia que el humano cotejará. Si
   fuera falso (el MCP espera otro formato), el ingeniero ajusta el string del ref sin cambiar
   el diseño. — Fundamento: el ledger de la corrida ES el RUN-LEDGER que la tool nombra.
5. **El mecanismo se shipea completo en `lucky-skills` sin escribir al saber** — `/saber
   citar` DEFINE la llamada a `saber_telemetria` (contrato, args, ref), pero el ACTO de
   dispararla es del consumidor (una sesión con el connector + endoso humano), no de esta
   corrida. Shipear la definición YA cierra el hueco declarado ("no hay campo que pregunte");
   el firing en vivo es del lane saberes (RAG↔Hackaton). Si fuera falso (definir sin poder
   disparar nunca deja el loop abierto), haría falta que el lane saberes lo consuma — que es
   justo su encargo. — Fundamento: límite del operador 2026-07-24 ("cuidado con lo de
   saberes"); el eje CAPTURA/BITACORA ya prueba que shipear el campo-de-juicio basta para que
   el hábito arranque.

**Corregime ahora o sigo con esto.**

---
id: adr:0019
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-gobierno-observable, adr:0016, adr:0018]
---

# 0019 — Gobierno observable: concejos, decisiones convocables, tablero, telemetría y frescura

## Contexto

Cuatro dolores del operador (debate 2026-07-16): los veredictos de concejos
multi-agente ("oro puro — el estudio de un caso desde varios ángulos") mueren
en directorios temporales de sesión; las decisiones que el operador toma en el
chat se pierden al cerrar la sesión; con muchas tablas no hay UNA vista de
"¿qué está abierto y qué espera MI juicio?" (el operador se abruma); y nada
mide qué reglas se usan (ley muerta) ni cuáles dejaron de ser verdad (ley
falsa — STALE 2026: los agentes no detectan solos el saber viciado).

## Decisión

1. **Concejos archivados**: todo panel multi-agente (diseños+jueces,
   investigaciones con síntesis) termina con el ORQUESTADOR archivando su
   veredicto como fila `docs/concejos/<YYYY-MM-DD-slug>.md` (tabla ya
   declarada): columnas `pregunta`, `angulos`, `ganador`/`sintesis`,
   `injertos`, `riesgos`, `refs` (a qué corrida/decisión/feature alimentó),
   estado `CERRADO`. Rige para los concejos POSTERIORES a esta decisión
   (directiva del operador: sin rescate retroactivo).
2. **Decisiones convocables**: cuando un flujo necesita un juicio del operador
   que hoy quedaría solo en el chat, se CONVOCA: fila `decision` en estado
   `PROPUESTA` presentada al operador; su veredicto la flipea a `ACEPTADA` |
   `RECHAZADA`; deprecarla después = `SUPERSEDIDA` + `superseded_by`. La regla
   operativa vive como rama `crisol/ramas/003-decisiones-convocables` (nace
   `estable`: el operador la endosó en el debate y este ADR la deposita).
3. **Tablero del operador**: `docs/TABLERO.md` = PROYECCIÓN generada por
   `scripts/proyectar.py` — la bandeja de entrada: corridas ACTIVE, decisiones
   PROPUESTA (esperan juicio), ramas `canal: propuesta` (cuarentena — esperan
   endoso), hotfixes/microfixes abiertos, diagnósticos ABIERTOS y ramas
   `EN_DUDA` (frescura). Determinista: lista estados, no calcula edades con
   reloj (M6 intacta).
4. **Telemetría de uso (poda con evidencia)**: hook PostToolUse fail-open
   (`telemetria-uso.py`, cableado en el `hooks.json` del plugin) que registra
   la CARGA de troncos y ramas como líneas JSONL en
   `$XDG_DATA_HOME/lucky/telemetria/uso.jsonl` (local del operador, taller,
   jamás en el repo ni en la red). La cosecha revisa ramas con cero hits →
   candidatas a poda o a reescritura de gatillo. FAIL-OPEN total: cualquier
   excepción → silencio (un hook de métricas jamás bloquea trabajo).
5. **Frescura (contra la ley falsa)**: una corrida cuya evidencia CONTRADICE
   una rama activa (la receta no funcionó) debe, en su cierre, flipear esa
   rama a `EN_DUDA` (transición legal) y referirla — el tablero la muestra
   como juicio pendiente del operador. La poda por uso caza ramas MUERTAS;
   esta regla caza ramas EQUIVOCADAS.

## Consecuencias

- El oro de los concejos queda indexable y con refs — nada se pierde en temp.
- Las decisiones del operador quedan como filas consultables con historia.
- El operador abre `docs/TABLERO.md` (o la brújula lo señala) y ve TODO lo que
  espera su juicio en una vista — el abrumamiento baja a una lectura.
- La poda de ley muerta/falsa deja de ser intuición: telemetría + EN_DUDA.
- Deuda declarada: la brújula podría señalar el tablero al arrancar (una línea
  en su prosa — corrida futura chica); agregación multi-repo de telemetría =
  futuro saber.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).**

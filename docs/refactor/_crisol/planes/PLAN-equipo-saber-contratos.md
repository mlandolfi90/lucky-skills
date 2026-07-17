---
id: PLAN-equipo-saber-contratos
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-07-17
refs: [corrida:2026-07-17-equipo-saber, adr:0023, adr:0021, adr:0018, adr:0005]
nota: "FASE PIN — fijar los contratos ANTES de planificar (lección del RETRO de equipo-doc-v1, ratificada por el-verde-significa-algo: plan APPROVE a la 1ª)"
---
# PIN de contratos — corrida `2026-07-17-equipo-saber`

Un solo carril (skill `saber` y agente `destilador` comparten contrato: partir
en dos planes sería el REJECT automático de "dos planes que tocan el mismo
contrato"). Los pines fijan lo que el plan NO puede mover:

## PIN 1 — Nombres y hogares (el nombre es el de-ruteo)

- Agente: **`destilador`** → `plugins/lucky/agents/destilador.md`
  (fila `agente/1`, `estado: LIVE`, `dictamina: []` — NO es guardián del roster
  del Crisol: no corre dentro de la matriz de veredictos; es la clase
  "verificador de registro"-autor que estrenó el lector-cero, ADR 0021 último
  párrafo — acá, AUTOR de borradores).
- Skill: **`saber`** → `plugins/lucky/skills/saber/SKILL.md` — mismo nombre que
  el repo `lucky-saber` y que el prefijo de las tools MCP (`saber_*`): la
  gramática existente manda.
- El harness descubre agentes por directorio y NO lee `estado:` → todo llamador
  usa el nombre `destilador` tal cual (precedente manualizador-2).

## PIN 2 — Frontera con `bitacora` (anti-duplicación, fuente única)

- `bitacora` = CONSUMIR (buscar/ficha por síntoma) + CAPTURAR (doctrina de
  §Capturar) + ESPEJO local (regen/lint/stale). **Nada de eso se re-enuncia** en
  la skill nueva: se REFERENCIA por nombre+sección.
- `saber` = ADMINISTRAR el ciclo central: inbox → merge → CANDIDATE→LIVE →
  poda/ascenso + orquestar la destilación al cierre.
- Insumos disjuntos: `/bitacora cosechar` destila del **log del observador**
  (conteos, modos FRECUENCIA/INTENSIDAD); `/saber destilar` destila de los
  **artefactos de corrida** (filas, RETROs, postmortems, diagnósticos,
  microfixes). Complementarios; ningún plan los mezcla.
- `bitacora/SKILL.md` recibe UNA línea puntero (aditiva, en §Mantener) hacia
  `saber`. Nada más se le toca; el espejo local (INDEX/entries/SENALES) es
  READ-ONLY generado y NADIE lo edita.

## PIN 3 — Gobernanza (innegociable; directiva del operador 2026-07-17)

- `saber_proponer_ficha` (→ rama `mcp-inbox/*`, **jamás main** — por
  construcción del MCP, ya sancionado en bitacora §Capturar 1) es el ÚNICO acto
  de escritura que el flujo dispara sin endoso.
- `saber_mergear`, promoción CANDIDATE→LIVE y poda: SOLO con endoso del
  operador, **ficha por ficha** ("un sí no es un sí al lote"). La skill jamás
  batchea merges ni infiere endosos de contexto.
- El `destilador` NI SIQUIERA llama MCP: devuelve borradores; propone el flujo
  que lo spawneó. Tools read-only (sin `Write`/`Edit`); `Bash` solo lectura
  (git log/show) — y el test lo verifica mecánicamente.
- Fail-open sin MCP: los borradores van a `/idea` (parking local), nunca se
  pierden, nunca bloquean.

## PIN 4 — El gatillo no depende de memoria (y NO se vuelve gate)

- crisol §4 paso 8 «Destilación»: edición MÍNIMA — el chequeo de los
  disparadores objetivos (los de bitacora §Capturar: gap >30min ·
  re-derivación · drift hallado · costo agudo) se REGISTRA SIEMPRE al cierre en
  el campo `BITACORA:` de la proyección (refs propuestas o `N/A (sin
  disparador)`). Disparador con sí → spawn del `destilador`.
- **Prohibido**: ID nuevo en el catálogo §5, celda nueva en la matriz, bloqueo
  del gate por destilación ("meter el playbook como obligatorio pelearía con el
  jidoka" — crisol §4 paso 8, textual, se respeta). La dureza es la HUELLA, no
  un gate.

## PIN 5 — Tests (el CI los descubre por glob; nacen cubiertos)

- `plugins/lucky/skills/saber/tests/test-saber.sh` — el glob del CI
  (`plugins/lucky/skills/*/tests/test-*.sh`) lo corre sin tocar `.github/`
  (PIN 1 de la corrida anterior trabajando a favor).
- Prueba invariantes MECÁNICOS, no prosa: (a) frontmatter del `destilador`
  parsea y cumple `agente/1` con `estado: LIVE`; (b) su línea `tools:` NO
  contiene `Write` ni `Edit` (read-only por construcción — PIN 3); (c)
  `SKILL.md` de saber existe con sello de familia; (d) el cableado existe:
  crisol §4 paso 8 nombra al `destilador` y bitacora apunta a `saber`.
- `RED_GREEN` aplica en pleno: el rojo de cada aserto se PRUEBA A/B en worktree
  descartable (mutando el sujeto, p. ej. `tools:` con `Write`), no se declara.

## PIN 6 — Qué NO se toca

- El espejo local de bitacora (`INDEX.md`/`entries/`/`SENALES.md`) — generado.
- Los hooks `bitacora-push.sh` / `bitacora-observar.sh` y sus tests.
- Las tools MCP (viven en el server `lucky-mcp`, no en este repo).
- El catálogo §5 del crisol (cero IDs nuevos — PIN 4).
- La semántica de `TEST_COVERAGE: NONE` (deuda declarada en ADR 0022 §3,
  decisión del operador pendiente).
- `plugins/lucky/.orphaned_at` (untracked pre-existente, backlog).

## Ratificaciones que NO se re-litigan

- Endoso ítem-por-ítem del operador para TODO merge al saber (directiva dura
  2026-07-17) — la skill lo lleva grabado, no lo re-discute.
- Citar por ancla de texto, no por número de línea puro (RETRO equipo-doc-v1).
- El cierre son DOS commits (hallazgo parkeado 2026-07-17: fila ACTIVE +
  `runState: closing` en el commit con código; `estado: CLOSED` en commit de
  docs posterior; editar una fila ya sellada = sello ROTO M8).

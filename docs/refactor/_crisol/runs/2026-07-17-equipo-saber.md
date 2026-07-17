---
id: 2026-07-17-equipo-saber
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-17
branch: main
titulo: "El saber tiene equipo — agente destilador + skill saber"
tier: "completo (2 artefactos canónicos nuevos + cableado en la ley del crisol = contrato; >1 archivo; establece patrón: el ciclo de vida del conocimiento tiene dueño)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (uniforme — fijado por el operador en el /goal: 'utiliza agentes opus pero tu el lider utiliza fable 5'; el líder corre en fable, fuera de la compuerta)"
ley: "v2.6.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "1/3 (convergió a la PRIMERA: PIN + arqueología previa → plan APPROVE 1ª + roster 4/4 PASS 1ª — primera corrida de la serie que no quema ni una iteración)"
runState: closing
cierre: "2026-07-17 · commit de cierre + forja v2.7.0 + tag anotado + GitHub Release; estado CLOSED en commit de docs posterior (mecánica de DOS commits, hallazgo 2026-07-17)"
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (directiva durable del operador para este repo; la corrida crea .md + tests shell que corren acá y en el CI)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "opus (uniforme) — dictado por el operador en el /goal 2026-07-17"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward, evidencia: "shift-left: A/B/C AGREGAN archivos nuevos; D = edición mínima ~8 líneas del bloque Destilación §4 paso 8 como caso (c) pagado con ADR 0023; E = puntero aditivo. Ninguna unidad estable se muta para extenderla"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward, evidencia: "shift-left: destilador = 1 responsabilidad (destila, read-only, sin MCP: juicio separado del acto = una garganta de escritura); saber COMPONE subcomandos de responsabilidad única"}
  - {regla: COSTURA, veredicto: PASS, quien: steward, evidencia: "shift-left: extensión donde el sistema varía (eje aprender, espejo del manualizador); cero especulación — poda/ascenso GUIADOS v1, telemetría diferida, cero ID de matriz, inbox no-enumerable declarado como deuda en vez de construir maquinaria"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "shift-left: único toque a estable es D (crisol §4 paso 8) = caso (c) contrato + ADR 0023; E aditivo puro; A/B/C AGREGAN. Etiquetas del plan correctas"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0023 sellado (ACEPTADA), frontmatter válido, refleja lo implementado (subcomandos, gate_check dry-run, guiados v1, bandeja local); refs recíprocas corrida↔ADR↔agente verificadas; ningún patrón normativo vive solo en prosa"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor-2, evidencia: "14/14 suites corridas por él en pc-local (TARGET declarado), todas exit 0 — incluida la nueva saber/test-saber 7/7; gates registros-lint + proyectar --check + leak-scan --staged exit 0; intérprete SONDADO (python3 = stub MS Store exit 49 → python 3.12)"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-2, evidencia: "14 runners: bitacora(4) cargar(1) crisol(6) ley(1) management(1) saber(1, NUEVA) — la corrida AGREGA cobertura, no es NONE"}
  - {regla: RED_GREEN, veredicto: PASS, quien: quality-auditor-2, evidencia: "test-saber.sh citado (único test del diff, 7 asserts): A/B en worktree descartable — verde exit 0 (7 PASS) con el código staged / rojo exit 1 (7 FAIL, cada assert por SU razón) contra base. 7/7 resueltos por nombre; repo real intacto"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0 (full-tree y --staged); 6 staged + 3 meta-docs + msg de commit barridos a mano; firmas (ghp_/sk-/AKIA/xox/eyJ/BEGIN/conn-strings) cero hits; ramas mcp-inbox/<hash> aclaradas como identificadores, no credenciales"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "5 frescos (Steward + 4 verificadores), input = artefactos reales (índice staged, PINes, fila) — nunca la prosa del paso previo; el auditor re-probó el rojo él mismo, no confió en el A/B del ingeniero"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "índice = EXACTAMENTE los 6 archivos del plan, 1:1; crisol = 1 solo hunk acotado al bloque Destilación (PIN 4 respetado: sin ID §5, sin celda, sin gate); bitacora = 1 bullet aditivo; .orphaned_at NO viaja"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "todo lo diferido tiene captura viva en ADR 0023 §Deuda (guiados v1, telemetría, inbox no-enumerable) y el descarte deliberado (ID DESTILACION) lleva su condición de reapertura (kaizen ~3 RETROs)"}
  - {regla: LISKOV, veredicto: "N/A", quien: design-verifier, evidencia: "destilador se spawnea POR NOMBRE, no bajo clave de dispatch; dictamina: [] lo deja fuera del roster polimórfico — sin relación de sustituibilidad que juzgar"}
  - {regla: INTERFACE_SEGREGATION, veredicto: "N/A", quien: design-verifier, evidencia: "el diff CONSUME el contrato saber_* (vive en lucky-mcp, fuera del repo — PIN 6); la salida del destilador tiene un único cliente (/saber destilar). Ningún contrato multi-cliente nuevo"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "cero manifiestos de dependencias en el diff; PyYAML es dep pre-existente de la suite; fail-closed presente (test aborta NO-verde si falta python/PyYAML)"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 1/3 — plan APPROVE a la 1ª y roster 4/4 PASS a la 1ª; cero iteraciones quemadas"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "commit de cierre tras PASS de los 4 verificadores frescos + Steward APPROVE; sin paralelo → sin Verificador de Integración"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "artefactos .md de ley + 1 suite shell; sin capas hexagonales que juzgar"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "pc-local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "re-sello uniforme a v2.7.0 por forjar-release.sh (incluye los 2 artefactos nuevos, que nacieron con ancla v2.6.0); pre-flight del universo SEALED"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "sellos + registry.json (saber entra sola por glob) + gates fail-closed en UNA pasada — nada a mano"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "v2.7.0 nace tras esta corrida con matriz completa y PASS de los 4 frescos (CLOSED en el commit de docs inmediato — mecánica de dos commits)"}
refs: [adr:0023, adr:0021, adr:0020, adr:0018, adr:0005]
---
- ORIGEN: pregunta del operador — *"tenemos lucky-saber pero ¿tenemos
  skills-agente para eso?"* — y el inventario que la respondió: de las lecciones
  de la sesión 2026-07-17, **2 fichas quedaron en mcp-inbox sin mergear, 3 en el
  parking, 1 solo en un RETRO sellado, 0 en LIVE**. Documentar ≠ aprender: solo
  la bitácora LIVE se consulta por síntoma, y no hay nadie cuyo trabajo sea
  llevar las lecciones ahí. La asimetría tiene espejo exacto: documentar-para-usar
  ganó equipo ayer (manualizador-2 + lector-cero + gate, ADR 0021);
  documentar-para-aprender sigue siendo "el líder, si se acuerda"
  (crisol §4 paso 8, "opcional, NO bloqueante" — hoy mismo NO se acordó).
  Mandato: /goal del operador 2026-07-17 — "planifica y ejecuta sin mi
  intervencion la creacion de un agente y una skill para
  (saber/aprendizaje/conocimiento) utiliza agentes opus pero tu el lider
  utiliza fable 5". La delegación cubre la CREACIÓN; la gobernanza del saber
  (qué entra a main, qué es verdad) queda donde estaba: en el operador
  ("tu no vas a cosechar nada que yo no entienda y autorice", 2026-07-17).
- Alcance (CERRADO):
  1. **Agente canónico `destilador`** (`plugins/lucky/agents/destilador.md`,
     fila `agente/1`) — el espejo del manualizador para el eje aprender: lee los
     ARTEFACTOS de la corrida/sesión (fila, RETRO, postmortems, diagnósticos,
     microfixes) y devuelve BORRADORES de ficha con el shape de
     `saber_proponer_ficha`, o "NADA COSECHABLE: <por qué>". Read-only: no llama
     MCP, no escribe archivos — el juicio es suyo, el acto de proponer es del
     flujo que lo spawnea.
  2. **Skill `saber`** (`plugins/lucky/skills/saber/SKILL.md` +
     `tests/test-saber.sh`) — administra el ciclo del conocimiento central:
     estado · revisar inbox (endoso POR FICHA → `saber_mergear`) · promover
     CANDIDATE→LIVE (solo a orden) · podar/ascender (presenta, decide el
     operador) · destilar (spawnea al `destilador` y propone al inbox).
  3. **Cableado del gatillo** — crisol §4 paso 8 «Destilación»: el chequeo de
     disparadores objetivos pasa de "opcional si el líder se acuerda" a
     "chequeo con REGISTRO": el campo `BITACORA:` se escribe SIEMPRE al cierre
     (refs propuestas o `N/A (sin disparador)`). Sin gate nuevo, sin ID de
     matriz nuevo. + 1 línea puntero en bitacora §Mantener.
  4. **ADR 0023** — la decisión y su porqué.
- MIGRATION_STRATEGY: N/A (sin DDL)
- NOTA working tree: `plugins/lucky/.orphaned_at` untracked PRE-existente
  (backlog, ya nombrado por 3 verificadores en corridas previas; NO es de esta
  corrida y no se toca).
- BITACORA: N/A (sin disparador — ESTRENO del paso 8 nuevo sobre la corrida que
  lo creó: 1/3 sin gap >30min, sin re-derivación, sin drift, sin costo agudo. El
  límite del inbox no-enumerable quedó en ADR 0023, no como ficha: es hallazgo
  de arqueología, todavía sin dolor real que lo valide — "sin evidencia real,
  no entra". La destilación de la corrida ANTERIOR (el-verde, que SÍ tuvo
  disparadores) corre como estreno de /saber destilar tras el cierre.)
- RETRO: la única fricción fue del LÍDER, no del proceso: la proyección
  TABLERO.md quedó fuera del commit E-open (la regla transaccional "mutación +
  proyecciones viajan JUNTAS" se salvó a mano con un commit inmediato). Ni el
  gate ni la forja cazan una proyección desincronizada en un commit intermedio
  — si se repite, es candidato a chequeo mecánico (proyectar --check en
  pre-commit, no solo en CI/forja). Lo demás: PIN + arqueología ANTES de
  planificar = primera corrida de la serie en converger 1/3 sin quemar
  iteraciones — el patrón queda ratificado dos corridas seguidas.

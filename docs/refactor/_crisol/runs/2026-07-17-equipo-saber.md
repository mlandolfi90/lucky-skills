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
iteraciones: "1/3 (en curso — plan APPROVE a la 1ª: la FASE PIN volvió a pagar)"
runState: wip
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (directiva durable del operador para este repo; la corrida crea .md + tests shell que corren acá y en el CI)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "opus (uniforme) — dictado por el operador en el /goal 2026-07-17"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward, evidencia: "shift-left: A/B/C AGREGAN archivos nuevos; D = edición mínima ~8 líneas del bloque Destilación §4 paso 8 como caso (c) pagado con ADR 0023; E = puntero aditivo. Ninguna unidad estable se muta para extenderla"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward, evidencia: "shift-left: destilador = 1 responsabilidad (destila, read-only, sin MCP: juicio separado del acto = una garganta de escritura); saber COMPONE subcomandos de responsabilidad única"}
  - {regla: COSTURA, veredicto: PASS, quien: steward, evidencia: "shift-left: extensión donde el sistema varía (eje aprender, espejo del manualizador); cero especulación — poda/ascenso GUIADOS v1, telemetría diferida, cero ID de matriz, inbox no-enumerable declarado como deuda en vez de construir maquinaria"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "shift-left: único toque a estable es D (crisol §4 paso 8) = caso (c) contrato + ADR 0023; E aditivo puro; A/B/C AGREGAN. Etiquetas del plan correctas"}
  - {regla: CREDITO, veredicto: PASS, quien: steward, evidencia: "shift-left: ADR 0023 depositado (ACEPTADA) y referenciado por A, D y E; el plan ordena incorporarle el límite del inbox no-enumerable como deuda declarada"}
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
- RETRO: <al cerrar>

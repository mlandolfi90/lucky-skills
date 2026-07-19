---
id: 2026-07-18-cosecha-agent-skills
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-18
branch: main
titulo: "Cosecha agent-skills: 6 piezas endosadas (pin de ejecución, DESAPARECE, supuestos, escenarios de endoso, superficie INDEX, piso de rondas)"
tier: "fast-path en serie (6 piezas chicas endosadas ítem por ítem por el operador; cada pieza = commit atómico F1..F6; las que agudizan semántica de la ley — F2 DESAPARECE, F3 supuestos — pagan con ADR 0024/0025)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (ingenieros; orden del operador 'usa agentes opus') — líder fable"
ley: "v2.7.0 (sello local == último tag)"
iteraciones: "1/3 (6 piezas F1..F6, ninguna rebotó; única corrección en caliente: test-pin-scan se auto-detectaba al entrar al árbol → auto-exclusión de sus fixtures)"
runState: closed
cierre: "2026-07-18 · commits 5e9560f (apertura) + 1760bf7 (F1) + 14f33d3 (F2) + 827472f (F3) + 4d879c8 (F4) + 74187d9 (F5) + 8041970 (F6) + cierre. Re-sello/tag DIFERIDO al próximo forjar-release.sh del operador."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: lider, evidencia: "pc-local (directiva durable del operador para lucky-skills)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus en los 6 ingenieros + 6 desarrolladores previos (orden del operador); líder fable"}
  - {regla: REGLA0, veredicto: PASS, quien: lider, evidencia: "en pc-local (TARGET): 17/17 suites exit 0 (batería completa corrida por el líder; test-lint 72s, lenta pero verde) + registros-lint 0 + proyectar --check byte-idéntico + leak-scan LIMPIO"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: lider, evidencia: "la corrida AGREGA 3 suites: test-pin-scan (crisol), test-racionalizaciones (cumplimiento, PRIMERA de esa skill), test-superficie-index (bitacora) — 14→17 runners"}
  - {regla: RED_GREEN, veredicto: PASS, quien: lider, evidencia: "los 3 tests nuevos vieron el rojo: pin-scan cazó diseno:41 y :68 ANTES del fix (reportado por el ingeniero F1); superficie-index falló contra sandbox con header mutado (A0 permanente); racionalizaciones verifica ids reales (A2 habría fallado con id inexistente). pin-scan y superficie-index llevan el red-proof DENTRO del test (el detector se prueba a sí mismo)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: lider, evidencia: "leak-scan --staged LIMPIO en cada commit F1..F6 + árbol completo LIMPIO al cierre; escenarios y ADRs sin valores sensibles"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: lider, evidencia: "F1/F2/F3 editan prosa de ley bajo caso legal (c) contrato pagado con ADR 0024/0025 (F2, F3) o precisión de regla existente sin ID nuevo (F1: PIN_TOTAL agudizada); F4/F5/F6 aditivos puros (escenarios, tests, regla dura nueva)"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: lider, evidencia: "6 piezas = exactamente las 6 endosadas ('aplica cada uno por uno'); la variante cara de F5 (fila SUPERFICIE_CONSUMIDOR) NO se hizo (descartada como generalidad especulativa); el ID SUPUESTOS NO se creó (decisión ADR 0025)"}
  - {regla: CREDITO, veredicto: PASS, quien: lider, evidencia: "ADR 0024 (DESAPARECE) y ADR 0025 (supuestos) ACEPTADAS con refs recíprocas a esta corrida; F1 precisa regla existente (sin ADR, correcto); enmienda a la receta [DECIDIDO 2026-07-06] registrada en IDEAS.md"}
  - {regla: PIN_TOTAL, veredicto: PASS, quien: lider, evidencia: "la corrida no agrega dependencias; al contrario, cierra el floating de diseno:41/:68 y deja test-pin-scan de guardia (árbol limpio: A1 PASS)"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras 17/17 + gates verdes"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no toca UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no toca código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "la corrida NO habilita release (re-sello diferido al operador)"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "no se crea tag"}
retro: "El gate del Crisol bloqueó al ingeniero F1 al intentar escribir el .sh sin corrida ACTIVE — y el ingeniero NO lo evadió: escribió el test en scratchpad y lo reportó. El sistema funcionó exactamente como fue diseñado (jidoka contra el propio equipo). Fricción real: el líder abrió la corrida DESPUÉS de lanzar F1 — la apertura debió preceder al primer ingeniero. Segunda fricción repetida: TABLERO.md (proyección) quedó fuera del commit de apertura otra vez (misma del RETRO de equipo-saber) — patrón: correr proyectar.py ANTES de commitear la apertura, no después."
bitacora: "N/A (sin disparador: ninguna suite mintió, ningún grep sin mapa, ningún drift doc↔código sufrido EN la corrida; la fricción TABLERO ya está capturada en el RETRO de equipo-saber)"
origen: "análisis de github.com/addyosmani/agent-skills (2 workflows: 176 agentes, 91 candidatos, 83 colisionados) → 6 sobrevivientes desarrollados por 6 agentes opus, colisiones verificadas por el líder contra los archivos reales, endoso del operador: 'aplica cada uno por uno. usa agentes opus.'"
alcance: "F1 crisol §Pin total + fila PIN_TOTAL + diseno paso 2 + test-pin-scan.sh (enmienda a receta [DECIDIDO 2026-07-06] de IDEAS.md) · F2 crisol §2 caso legal (b) DESAPARECE + design-verifier bullet 3 + anti-patrones fila + ADR 0024 · F3 crisol Paso 3/4 supuestos (tope 5, solo tier completo) + steward 3-bis + collision-map premisas + escenario + ADR 0025 · F4 cumplimiento escenarios/endoso.md + tabla racionalizaciones GUIA-SKILLS + test-racionalizaciones.sh · F5 bitacora tests/test-superficie-index.sh (header + aridad del INDEX real) · F6 feature regla dura 6 (piso de rondas N=3)"
nota_release: "la propagación a sesiones es por TAG; el re-sello de la familia + tag quedan DIFERIDOS al próximo forjar-release.sh del operador (mismo criterio que la corrida regla-dedup-key-estable)"
---

Corrida abierta. Trabajo por piezas F1..F6, un ingeniero opus por pieza, el
líder verifica y commitea entre pieza y pieza. Matriz al cierre.

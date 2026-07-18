---
id: 2026-07-17-regla-dedup-key-estable
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-17
branch: main
titulo: "Regla dura: dedup_key estable (kebab-case de la lección) en la skill bitacora"
tier: "fast-path (1 skill .md, prosa aditiva; sin código, sin contrato, sin tests tocados)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (uniforme — la sesión del líder corre en opus; agentes opus)"
ley: "v2.7.0 (verificada — clon al día con origin/main f32d45b; último tag v2.7.0)"
iteraciones: "1/3"
runState: closing
cierre: "2026-07-17 · commits 191dddf (apertura+skill) + este (cierre). Re-sello/tag DIFERIDO al próximo release del operador."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: lider, evidencia: "pc-local (directiva durable del operador para lucky-skills — la forja corre local)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus (uniforme) — la sesión corre en opus"}
  - {regla: REGLA0, veredicto: PASS, quien: lider, evidencia: "en pc-local (TARGET): leak-scan --staged LIMPIO + registros-lint 0 hallazgos + proyectar --check al día + test-ruteo 16 troncos/4 ramas exit 0. Prosa .md: sin suite propia; la sanidad de ruteo confirma que el árbol sigue navegable"}
  - {regla: TEST_COVERAGE, veredicto: N/A, quien: lider, evidencia: "cambio de PROSA en una skill; no crea ni modifica tests"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: lider, evidencia: "leak-scan.sh --staged (la MISMA herramienta del leak-verifier) LIMPIO + revisión de las 16 líneas: dedup_key/kebab-case/ejemplos (git-commit-backticks), cero valores sensibles. Fast-path de prosa → gate mecánico proporcionado en vez de subagente"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: lider, evidencia: "aditivo puro: se AGREGA una instrucción en §Capturar + un recordatorio en §Reglas duras; ninguna regla existente se edita ni borra"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: lider, evidencia: "1 archivo (bitacora/SKILL.md); no se forjó tag ni se tocó otra skill — el re-sello se diferió deliberadamente"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras gates verdes"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: N/A, quien: gate, evidencia: "no toca UI"}
  - {regla: CONFORMIDAD, veredicto: N/A, quien: gate, evidencia: "no toca código hexagonal"}
  - {regla: SELLOS, veredicto: N/A, quien: gate, evidencia: "la corrida NO habilita release (re-sello diferido al operador)"}
  - {regla: TAG_GATE, veredicto: N/A, quien: gate, evidencia: "no se crea tag en esta corrida"}
refs: [adr:0004]
---
- ORIGEN: el operador eligió "en la ley (skill bitacora)" para la regla #3 del programa de optimización del saber (contraparte de PREVENCIÓN del feature de DETECCIÓN cerrado hoy en lucky-tool-saber, ADR 0004). Diagnóstico: el saber deduplica por fingerprint LITERAL del contenido → dos redacciones de la misma lección = duplicado; un scan real halló el caso genuino (CAND-c59755~CAND-4e991@79%, leak-scan).
- Alcance: UN archivo, `plugins/lucky/skills/bitacora/SKILL.md` — se agrega la instrucción "`dedup_key` SIEMPRE explícito y estable, kebab-case de la LECCIÓN no de la redacción" en §Capturar (punto 1) + un recordatorio en §Reglas duras. Prosa aditiva; ninguna regla existente se edita/borra.
- RELACIÓN CON EL FEATURE: PREVENCIÓN (esta regla, en origen) + DETECCIÓN (el aviso de casi-duplicado en saber_mergear, ADR 0004). El texto lo cruza explícitamente ("prevenir es más barato que curar").
- NOTA-RELEASE (importante): la propagación de una skill a las sesiones es por TAG (Ley viva = último tag). Este cambio va a main; para que llegue a las sesiones y quede el SELLO consistente hace falta un release (forjar-release.sh re-sella TODA la familia). Dado que el operador está forjando lucky-skills ACTIVAMENTE hoy (v2.4→2.5→2.6→2.7 en el día), el re-sello + tag se DIFIERE a su próximo release para no pisar una forja en curso — NO se forja un vX.Y.Z en paralelo desde esta corrida. El próximo `forjar-release.sh` del operador recogerá este contenido y re-sellará bitacora automáticamente.
- MIGRATION_STRATEGY: N/A
- RETRO: el commit de apertura absorbió la skill porque quedó staged del leak-scan previo → apertura y trabajo cayeron juntos en 191dddf. En fast-path .md (exento del gate) no bloquea, pero la higiene pide stagear selectivo. Nada que reabrir. Y el punto de proceso importante: para que esta regla LLEGUE a las sesiones falta el release (las skills se cargan por tag) — se dejó para el próximo forjar-release.sh del operador, que re-sella toda la familia, en vez de forjar un tag en paralelo a su forja activa de hoy.

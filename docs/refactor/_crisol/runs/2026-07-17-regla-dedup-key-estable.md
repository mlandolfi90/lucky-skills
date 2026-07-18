---
id: 2026-07-17-regla-dedup-key-estable
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-17
branch: main
titulo: "Regla dura: dedup_key estable (kebab-case de la lección) en la skill bitacora"
tier: "fast-path (1 skill .md, prosa aditiva; sin código, sin contrato, sin tests tocados)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (uniforme — la sesión del líder corre en opus; agentes opus)"
ley: "v2.7.0 (verificada — clon al día con origin/main f32d45b; último tag v2.7.0)"
iteraciones: "0/3"
runState: wip
veredictos: []
refs: [adr:0004]
---
- ORIGEN: el operador eligió "en la ley (skill bitacora)" para la regla #3 del programa de optimización del saber (contraparte de PREVENCIÓN del feature de DETECCIÓN cerrado hoy en lucky-tool-saber, ADR 0004). Diagnóstico: el saber deduplica por fingerprint LITERAL del contenido → dos redacciones de la misma lección = duplicado; un scan real halló el caso genuino (CAND-c59755~CAND-4e991@79%, leak-scan).
- Alcance: UN archivo, `plugins/lucky/skills/bitacora/SKILL.md` — se agrega la instrucción "`dedup_key` SIEMPRE explícito y estable, kebab-case de la LECCIÓN no de la redacción" en §Capturar (punto 1) + un recordatorio en §Reglas duras. Prosa aditiva; ninguna regla existente se edita/borra.
- RELACIÓN CON EL FEATURE: PREVENCIÓN (esta regla, en origen) + DETECCIÓN (el aviso de casi-duplicado en saber_mergear, ADR 0004). El texto lo cruza explícitamente ("prevenir es más barato que curar").
- NOTA-RELEASE (importante): la propagación de una skill a las sesiones es por TAG (Ley viva = último tag). Este cambio va a main; para que llegue a las sesiones y quede el SELLO consistente hace falta un release (forjar-release.sh re-sella TODA la familia). Dado que el operador está forjando lucky-skills ACTIVAMENTE hoy (v2.4→2.5→2.6→2.7 en el día), el re-sello + tag se DIFIERE a su próximo release para no pisar una forja en curso — NO se forja un vX.Y.Z en paralelo desde esta corrida. El próximo `forjar-release.sh` del operador recogerá este contenido y re-sellará bitacora automáticamente.
- MIGRATION_STRATEGY: N/A

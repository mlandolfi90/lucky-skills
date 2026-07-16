---
id: 2026-07-16-gobierno-observable
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "v2.3.0 — T3: gobierno observable — concejos, decisiones convocables, tablero, telemetría, frescura"
tier: "completo (toca proyectar.py + hooks.json del plugin + establece patrones de gobierno)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.2.0 (recién forjada y publicada en esta sesión)"
iteraciones: "3/3"
runState: wip
veredictos: []
refs: [adr:0019, adr:0018, adr:0016]
---
- ORIGEN: tranche T3 del backlog aprobado (debate 2026-07-16: capturas "CONCEJOS como registro indexable", "Decisiones CONVOCABLES", "TABLERO del operador", "TELEMETRÍA de ramas", "frescura de ramas").
- Alcance: [T3a] ADR 0019 (gobierno observable). [T3b] concejos archivados: anatomía canónica de la fila concejo (tabla ya declarada) — el orquestador archiva el veredicto al completar TODO panel multi-agente (rige para los próximos, directiva del operador: sin rescate retroactivo). [T3c] rama crisol/003-decisiones-convocables (gatillo: el flujo necesita juicio del operador que quedaría solo en el chat) — nace estable: endoso previo del operador en el debate + ADR 0019. [T3d] proyectar_tablero(): docs/TABLERO.md GENERADO — la bandeja del operador: corridas ACTIVE, decisiones PROPUESTA, ramas en cuarentena, hotfix/microfix abiertos, diagnósticos ABIERTOS, ramas EN_DUDA (frescura); declarado en el manifiesto + lint; test-tablero.sh. [T3e] telemetría de uso: hooks/telemetria-uso.py (PostToolUse Read de ramas/troncos → JSONL en XDG ~/.local/share/lucky/telemetria/, FAIL-OPEN total, cero red) cableado en plugins/lucky/hooks/hooks.json — alimenta la poda de ley muerta. [T3f] frescura: regla "corrida que contradice una rama → EN_DUDA" depositada en ADR 0019 (el mecanismo EN_DUDA+⚠ ya existe de T2).
- MIGRATION_STRATEGY: N/A (sin DDL destructivo; el tablero es proyección nueva declarada)
- ITER-2: observaciones del design-verifier corregidas al instante — (1) test-tablero.sh entregado (9/9: marcador, ACTIVE listada/CLOSED no, decisión PROPUESTA, cuarentena, EN_DUDA, cross-check no-ruteo, idempotencia); (2) regex de telemetría ANCLADA a lucky/skills/ (un path de usuario con forma parecida jamás se loguea — probado: priv 0 eventos, ley 1 evento); (3) reconciliar la letra de ADR 0018 §2 con la vía endoso-por-decisión → parkeado.
- ITER-3: FAIL de SCOPE_CREEP del scope-verifier — (a) test-tablero.sh: ya entregado en iter-2 (9/9); (b) la regeneración del bloque RAMAS de crisol/SKILL.md (línea 003) estaba en el working tree SIN commitear (violación de la regla transaccional registro+proyección-mismo-commit) → commiteada acá. Lección directa a la regla que esta misma migración instauró: el gate del futuro (Fase 2) debería verificar working-tree-limpio-de-proyecciones en el commit, no solo el drift.

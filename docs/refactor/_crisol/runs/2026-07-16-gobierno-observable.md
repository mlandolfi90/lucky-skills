---
id: 2026-07-16-gobierno-observable
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "v2.3.0 — T3: gobierno observable — concejos, decisiones convocables, tablero, telemetría, frescura"
tier: "completo (toca proyectar.py + hooks.json del plugin + establece patrones de gobierno)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.2.0 (recién forjada y publicada en esta sesión)"
iteraciones: "3/3"
cierre: "2026-07-16 · commit de cierre + tag anotado v2.3.0 + GitHub Release"
runState: closing
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local, directiva de sesión"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "145 asserts (110+10+8+8+9) + 17 funcionales telemetría + sandbox cuarentena, exits reales, HEAD final en worktree prístino"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "5 suites + lints + forja dry + funcional TABLERO/TELEMETRÍA/hooks.json"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "3 frescos iter-1; remedios re-verificados por quality-auditor (agente distinto) en worktree prístino"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: quality-auditor, evidencia: "FAIL iter-1 (test faltante + proyección sin commitear) → iter-2 test-tablero 9/9 + iter-3 bloque commiteado; --check exit 0 en prístino de babe861; cero sobrantes"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0019 en el commit de apertura; refs recíprocas ambas direcciones verificadas"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "deudas con hogar (brújula→tablero; telemetría multi-repo; letra 0018§2 parkeada en IDEAS)"}
  - {regla: FIDELIDAD_ESPEC, veredicto: PASS, quien: scope-verifier, evidencia: "tablero=bandeja de juicio; concejos solo-próximos sin rescate; convocables ciclo completo; telemetría local probada; frescura depositada"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "sin DDL"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0; JSONL en vivo = {tipo,skill,rama,session[:16],ts} sin paths ni contenido; Read fuera de la ley NO registra; off-switch y fail-open probados"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "todo agregado; main() solo ganó la llamada (costura prevista)"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "proyectar.py 315<400 una responsabilidad; telemetria-uso.py 43L; separación .sh/.py forzada por restricción real documentada"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "sección nueva = una llamada seccion(); proyección nueva = función + llamada; elif de eventos = altitud correcta"}
  - {regla: LISKOV, veredicto: "N/A", quien: design-verifier, evidencia: "sin jerarquías"}
  - {regla: INTERFACE_SEGREGATION, veredicto: "N/A", quien: design-verifier, evidencia: "sin contratos multi-cliente; cada consumidor lee solo sus claves"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: design-verifier, evidencia: "rama 003 estable por endoso registrado en ADR 0019 ACEPTADA — espíritu de cuarentena satisfecho; reconciliación de letra parkeada"}
  - {regla: PIN_TOTAL, veredicto: PASS, quien: design-verifier, evidencia: "stdlib puro, sin red, sin pip"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 3/3 — dentro del techo"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "pre-flight 42 archivos 1 ancla (rama 003 incluida); re-sello uniforme v2.3.0"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.3.0 exit 0"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "tag anotado v2.3.0 tras CLOSED + matriz verde"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "cierre tras roster verde + remedios re-verificados"}
  - {regla: BUMP_REASON, veredicto: "N/A", quien: gate, evidencia: "sin bumps"}
refs: [adr:0019, adr:0018, adr:0016]
---
- ORIGEN: tranche T3 del backlog aprobado (debate 2026-07-16: capturas "CONCEJOS como registro indexable", "Decisiones CONVOCABLES", "TABLERO del operador", "TELEMETRÍA de ramas", "frescura de ramas").
- Alcance: [T3a] ADR 0019 (gobierno observable). [T3b] concejos archivados: anatomía canónica de la fila concejo (tabla ya declarada) — el orquestador archiva el veredicto al completar TODO panel multi-agente (rige para los próximos, directiva del operador: sin rescate retroactivo). [T3c] rama crisol/003-decisiones-convocables (gatillo: el flujo necesita juicio del operador que quedaría solo en el chat) — nace estable: endoso previo del operador en el debate + ADR 0019. [T3d] proyectar_tablero(): docs/TABLERO.md GENERADO — la bandeja del operador: corridas ACTIVE, decisiones PROPUESTA, ramas en cuarentena, hotfix/microfix abiertos, diagnósticos ABIERTOS, ramas EN_DUDA (frescura); declarado en el manifiesto + lint; test-tablero.sh. [T3e] telemetría de uso: hooks/telemetria-uso.py (PostToolUse Read de ramas/troncos → JSONL en XDG ~/.local/share/lucky/telemetria/, FAIL-OPEN total, cero red) cableado en plugins/lucky/hooks/hooks.json — alimenta la poda de ley muerta. [T3f] frescura: regla "corrida que contradice una rama → EN_DUDA" depositada en ADR 0019 (el mecanismo EN_DUDA+⚠ ya existe de T2).
- MIGRATION_STRATEGY: N/A (sin DDL destructivo; el tablero es proyección nueva declarada)
- ITER-2: observaciones del design-verifier corregidas al instante — (1) test-tablero.sh entregado (9/9: marcador, ACTIVE listada/CLOSED no, decisión PROPUESTA, cuarentena, EN_DUDA, cross-check no-ruteo, idempotencia); (2) regex de telemetría ANCLADA a lucky/skills/ (un path de usuario con forma parecida jamás se loguea — probado: priv 0 eventos, ley 1 evento); (3) reconciliar la letra de ADR 0018 §2 con la vía endoso-por-decisión → parkeado.
- ITER-3: FAIL de SCOPE_CREEP del scope-verifier — (a) test-tablero.sh: ya entregado en iter-2 (9/9); (b) la regeneración del bloque RAMAS de crisol/SKILL.md (línea 003) estaba en el working tree SIN commitear (violación de la regla transaccional registro+proyección-mismo-commit) → commiteada acá. Lección directa a la regla que esta misma migración instauró: el gate del futuro (Fase 2) debería verificar working-tree-limpio-de-proyecciones en el commit, no solo el drift.
- RETRO: la regla transaccional registro+proyección-mismo-commit se violó DOS veces en la sesión (T3 apertura y rama 003) y ambas las cazaron guardianes distintos — la disciplina no alcanza: la Fase 2 del gate debe verificar working-tree-limpio-de-proyecciones en el commit (parkeado). El bug heredoc-consume-stdin del hook casi viaja a la flota: probar hooks con stdin REAL antes de cablear, siempre.

---
id: 2026-07-16-refactor-arbol-registros
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "v2.0.0 — refactor árbol/registros: ledger por corrida + manifiesto + proyecciones"
tier: "completo (multi-archivo de código + cambia el patrón del sistema documental — la ley que viaja a la flota)"
target: "pc-local (Git-Bash del operador — forja la familia de skills; directiva del operador, debate 2026-07-16)"
model: "fable (uniforme — Compuerta del Paso 0 respondida por el operador en el debate)"
ley: "v1.41.0 (verificada contra remoto en esta sesión)"
iteraciones: "1/3"
runState: closing
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local, directiva explícita del operador"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme), Compuerta respondida en debate"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "7 verificaciones propias en pc-local: enforcer 110-0 · paridad 10-0 · atomicidad 8-0 · lint 0 · drift 0 · forja-dry 0 · sandbox 2x byte-idéntico"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "test-enforcer 110 + test-paridad 10 + test-atomicidad 8 + registros-lint + proyectar --check + forja dry + sandbox adopción"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "5 verificadores frescos (subagentes nuevos, fable), input = diff real a94b964..HEAD"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "20 archivos del diff mapean 1:1 a C1..C6; fix resolver Python = condición de C6"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "Fase 2 + poda tronco + backlog del debate en docs/IDEAS.md; obs del design-verifier parkeadas al instante"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0016 frontmatter decision/1 válido, refs recíprocas con esta fila, sellado"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "sin DDL en el diff"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0 (143 archivos) + 20 del diff a mano + mensajes de commit limpios"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "todo lo nuevo = archivos nuevos; guardianes intactos (fuera del diff); estables editados = casos legales con ADR 0016"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "proyectar 197L / lint 219L una responsabilidad c/u; >400 resueltos por nombre (forja larga-legítima; archivo congelado por diseño; SKILL.md 589 citado → deuda parkeada)"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "manifiesto = dato; render legacy aislado en _render_run marcada a morir en Fase 2; puerto DB diferido (sin especulación)"}
  - {regla: LISKOV, veredicto: PASS, quien: design-verifier, evidencia: "proyección = sustituto drop-in del ledger manuscrito ante el gate, probado conductualmente (paridad 10-0)"}
  - {regla: INTERFACE_SEGREGATION, veredicto: N/A, quien: design-verifier, evidencia: "sin contratos multi-cliente nuevos; el puerto de 4 ops deliberadamente NO se construyó"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: design-verifier, evidencia: "SKILL.md/forja/adoptar = refactor deliberado documentado en ADR 0016"}
  - {regla: PIN_TOTAL, veredicto: PASS, quien: design-verifier, evidencia: "PyYAML declarada (docstrings, 6.0.1 probado) y fail-closed en import/test/forja; tool de forja, no artefacto consumido"}
  - {regla: CONFORMIDAD, veredicto: PASS, quien: conformidad-verifier, evidencia: "hexagonal N/A honesto (tooling de proceso); ubicación scripts/ + naming coherente + deps sanas: verde"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "TARGET local sin @env (no paas)"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "la corrida no toca UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/producción"}
  - {regla: TECHO_ITER, veredicto: "N/A", quien: líder, evidencia: "1 iteración, sin ciclo Plan↔FAIL"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.0.0: pre-flight 28 archivos con 1 ancla exacta; re-sello uniforme a v2.0.0"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.0.0 exit 0: sellos + plugin.json + registry + leak-scan + bitacora-lint + sellado de corrida + registros-lint + no-drift"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "tag anotado v2.0.0 creado recién tras STATUS CLOSED + matriz completa verde"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "commit de cierre tras 5/5 veredictos PASS del roster fresco"}
  - {regla: BUMP_REASON, veredicto: "N/A", quien: gate, evidencia: "sin bump de pins de terceros"}
refs: [adr:0016]
cierre: "2026-07-16 · commit de cierre + tag anotado v2.0.0 + GitHub Release (título y notas)"
---
- ORIGEN: debate operador↔agente 2026-07-16 (capturas en docs/IDEAS.md) + concejo de diseño (3 diseños · 3 jueces → ganador git-nativo-mínimo con injertos) + concejo 4-criterios (12 mejoras). PLAY del operador: "aplicar la refactorización por pasos atómicos, terminar sin mi intervención, commits atómicos para rollback, tag final con título y notas".
- Alcance: migración aprobada (Punto 5 del debate), commits atómicos C1..C8: [C1] ADR 0016; [C2] docs/registros.yaml + .gitattributes + scripts/registros-lint.py; [C3] congelar monolito → runs/_archivo-hasta-2026-07.md + runs/2026-07-16-refactor-arbol-registros.md + scripts/proyectar.py (RUN-LEDGER.md pasa a PROYECCIÓN legacy en el MISMO path — cero cambios en guardianes) + _ACTIVE + prueba de paridad; [C4] skill crisol abre corridas como registros (prosa); [C5] huérfanos → planes/ con frontmatter estado; [C6] forja sella corridas CLOSED (sha256 LF) + adoptar-crisol siembra manifiesto write-if-absent; [C6b] fix de orden sellar→lint; [C7] roster de verificadores frescos (5/5 PASS); [C8] cierre + forja v2.0.0 + tag anotado + GitHub Release. FASE 2 del gate (guardianes leen frontmatter) = corrida FUTURA separada (decisión del debate: jamás juntas).
- MIGRATION_STRATEGY: N/A (sin DDL; migración de archivos reversible por commit atómico)
- RETRO: la corrida nació híbrida (abrió en formato legacy y se auto-migró a fila a mitad de camino — la próxima nace fila desde el Paso 2); el defecto de orden sellar↔lint de la forja apareció recién al ENSAYAR el cierre, no en el diseño: ensayar el cierre antes de codearlo debería ser paso del Planificador. El tronco de crisol subió a 589 líneas porque el mecanismo de ramas se decretó sin estrenarse — la primera rama debe adelgazarlo (parkeado).

---
id: 2026-07-16-ecosistema-features-migrar
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "v2.4.0 — T4: ecosistema — features, Manualizador, /migrar, evals de ruteo, métricas"
tier: "completo (skills nuevas + agentes + toca la forja + cierra el programa del debate 2026-07-16)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.3.0 (recién forjada y publicada en esta sesión)"
iteraciones: "2/3"
cierre: "2026-07-16 · commit de cierre + tag anotado v2.4.0 + GitHub Release"
runState: closing
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local, directiva de sesión"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "145 asserts + ruteo 15/3 + lints 0 + drift 0 + forja-dry 47 sellos exit 0, pc-local"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "6 suites + lints + metricas + prueba negativa: gatillo duplicado → exit 1 R3"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "2 verificadores frescos (quality + triple design/leak/scope)"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "mapeo T4a..T4f 1:1; cero sobrantes/faltantes"}
  - {regla: FIDELIDAD_ESPEC, veredicto: PASS, quien: scope-verifier, evidencia: "capturas del operador punto por punto (feature/manualizador/migrar/evals/métricas)"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0020 al abrir; refs recíprocas ambas direcciones; nit del curador → deuda declarada en iter-2"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "deudas con hogar (evals LLM, render por-app, M4, curador)"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "sin DDL"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0; ALL-SECRETS citado solo como patrón de nombre con doctrina en la misma frase; 559 líneas limpias"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "todo agregado; forja +10 anexas con if-exists (caso legal declarado en plan)"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "75/76/46/51/70/112 líneas; una responsabilidad c/u; fronteras feature↔idea y migrar↔adoptar nítidas"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "eval nuevo = bloque R-N; métrica nueva = print-block; forja invoca por if-exists"}
  - {regla: LISKOV, veredicto: PASS, quien: design-verifier, evidencia: "2 agentes nuevos honran el contrato agente/1 (mismo shape que crisol-*)"}
  - {regla: INTERFACE_SEGREGATION, veredicto: PASS, quien: design-verifier, evidencia: "clasificador SIN Write/Edit (solo propone); manualizador CON (su rol escribe)"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: design-verifier, evidencia: "única edición a estable = sección anexa de forja, declarada en T4e"}
  - {regla: PIN_TOTAL, veredicto: PASS, quien: design-verifier, evidencia: "cero deps nuevas; promptfoo NO entró (deuda pineada)"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 2/3 (nits aplicados en iter-2)"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "pre-flight 47 archivos 1 ancla; re-sello uniforme v2.4.0"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.4.0 exit 0 con test-ruteo cableado"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "tag anotado v2.4.0 tras CLOSED + matriz verde"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "cierre tras 2 verificadores frescos PASS + nits aplicados"}
  - {regla: BUMP_REASON, veredicto: "N/A", quien: gate, evidencia: "sin bumps"}
refs: [adr:0020, adr:0019, adr:0018, adr:0017, adr:0016]
---
- ORIGEN: tranche T4 — última del programa del debate 2026-07-16 (capturas: "FEATURES como registro de primera clase", "AGENTE DOCUMENTADOR (Manualizador)", "DOCUMENTACIÓN por soft para TRES audiencias", "SKILL-AGENTE DE MIGRACIÓN", "EVALS de la ley EXTENDIDOS", "MÉTRICAS DE ÉXITO M1-M8/M9").
- Alcance: [T4a] ADR 0020 (ecosistema). [T4b] skill `feature`: lo-que-el-proyecto-debe-tener como registro de primera clase (nacimiento, evolución, intentos, sub-features vía padre:, NUNCA cierra) — promoción desde idea madura; gate de doc: no llega a VIVA sin su doc. [T4c] agente canónico `manualizador` (nombre del operador): mantiene docs/manual (user) + docs/sistema (dev) renderizables en la app desde fuente única; gatillos ESTRICTOS: feature→VIVA u orden explícita — jamás documenta trabajo inestable; narrativa producto declarada en el manifiesto. [T4d] skill `migrar` + agente canónico `migrar-clasificador`: retrofit de repos pre-2.0 — inventariar → clasificar contra registros.yaml → proponer mapeo → ENDOSO del operador (decisión convocable) → congelar monolitos verbatim / adoptar huérfanos / lint a 0; jamás mueve sin endoso; complementa a adoptar-crisol (siembra) — este ORDENA lo viejo. [T4e] evals de ruteo mecánicos: test-ruteo.sh (gatillos únicos/no-vacíos por skill, descriptions con disparadores) cableado fail-closed en la forja; evals LLM (promptfoo pineado) = deuda declarada. [T4f] scripts/metricas.py: reporte M1-M9 (troncos, corridas, huérfanos, evals, idempotencia, paridad, sellos, presupuesto de contexto por activación) — report-only, baseline del programa.
- MIGRATION_STRATEGY: N/A (sin DDL destructivo; tablas feature/agente ya declaradas desde v2.0.0)
- ITER-2: nits de los verificadores aplicados — curador de features a deuda declarada de ADR 0020; import io muerto removido de metricas.py; RUTEO_REPO_OVERRIDE conservado (SÍ tiene usuario: el quality-auditor lo usó para la prueba negativa en sandbox).
- RETRO: cierre del programa del debate 2026-07-16 (C1..C8 + T1..T4, 5 releases v2.0.0→v2.4.0 en una sesión): el patrón ADR-al-abrir eliminó los FAIL de CREDITO desde T2; la regla transaccional sigue siendo el punto frágil humano/agente (2 violaciones cazadas) — Fase 2 del gate es la próxima corrida natural.

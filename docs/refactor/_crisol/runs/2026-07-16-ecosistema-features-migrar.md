---
id: 2026-07-16-ecosistema-features-migrar
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "v2.4.0 — T4: ecosistema — features, Manualizador, /migrar, evals de ruteo, métricas"
tier: "completo (skills nuevas + agentes + toca la forja + cierra el programa del debate 2026-07-16)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.3.0 (recién forjada y publicada en esta sesión)"
iteraciones: "1/3"
runState: wip
veredictos: []
refs: [adr:0020, adr:0019, adr:0018, adr:0017, adr:0016]
---
- ORIGEN: tranche T4 — última del programa del debate 2026-07-16 (capturas: "FEATURES como registro de primera clase", "AGENTE DOCUMENTADOR (Manualizador)", "DOCUMENTACIÓN por soft para TRES audiencias", "SKILL-AGENTE DE MIGRACIÓN", "EVALS de la ley EXTENDIDOS", "MÉTRICAS DE ÉXITO M1-M8/M9").
- Alcance: [T4a] ADR 0020 (ecosistema). [T4b] skill `feature`: lo-que-el-proyecto-debe-tener como registro de primera clase (nacimiento, evolución, intentos, sub-features vía padre:, NUNCA cierra) — promoción desde idea madura; gate de doc: no llega a VIVA sin su doc. [T4c] agente canónico `manualizador` (nombre del operador): mantiene docs/manual (user) + docs/sistema (dev) renderizables en la app desde fuente única; gatillos ESTRICTOS: feature→VIVA u orden explícita — jamás documenta trabajo inestable; narrativa producto declarada en el manifiesto. [T4d] skill `migrar` + agente canónico `migrar-clasificador`: retrofit de repos pre-2.0 — inventariar → clasificar contra registros.yaml → proponer mapeo → ENDOSO del operador (decisión convocable) → congelar monolitos verbatim / adoptar huérfanos / lint a 0; jamás mueve sin endoso; complementa a adoptar-crisol (siembra) — este ORDENA lo viejo. [T4e] evals de ruteo mecánicos: test-ruteo.sh (gatillos únicos/no-vacíos por skill, descriptions con disparadores) cableado fail-closed en la forja; evals LLM (promptfoo pineado) = deuda declarada. [T4f] scripts/metricas.py: reporte M1-M9 (troncos, corridas, huérfanos, evals, idempotencia, paridad, sellos, presupuesto de contexto por activación) — report-only, baseline del programa.
- MIGRATION_STRATEGY: N/A (sin DDL destructivo; tablas feature/agente ya declaradas desde v2.0.0)

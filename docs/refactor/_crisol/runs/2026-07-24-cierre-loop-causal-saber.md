---
id: 2026-07-24-cierre-loop-causal-saber
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-24
branch: main
titulo: "Cerrar el loop causal del saber — subcomando /saber citar + campo CITAS_SABER en el cierre (espejo de BITACORA)"
tier: "completo (toca el ritual de cierre del Crisol §4 = contrato; agrega subcomando a saber + campo de cierre + campo al template; norma nueva → ADR 0027; >1 archivo)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder + subagentes; el operador está en opus-4.8) — corrida en goal mode 'dejar funcional'"
ley: "v2.9.0 (sello local == último tag)"
iteraciones: "1/3"
runState: wip
origen: "encargo cross-sesión de 'Evaluación de arquitecturas RAG (fork 2)', endosado por el operador (goal 'dejar funcional'). Problema MEDIDO por esa sesión con saber_metricas (2026-07-24): de ~50 fichas, las consultas fluyen (DRIFT-004/FALSO-VERDE-004 con 16, DRIFT-001 con 13) pero las citas causales están en 0 salvo DRIFT-001 (2). El loop consulta→refuerzo no cierra: saber_telemetria existe y nadie lo llama."
alcance: "A. ADR 0027 (decisión: el cierre registra SIEMPRE las citas causales, espejo de BITACORA/destilación — CAPTURA ya cableada, REFUERZO no) · B. saber/SKILL.md subcomando nuevo /saber citar (define el cómo: fichas consultadas en la sesión → endoso humano de cuáles funcionaron → saber_telemetria con el run_ledger_ref) · C. crisol/SKILL.md §4 paso 8 puntero + campo CITAS_SABER registrado siempre (citas o N/A) · D. template run-ledger.md agrega CITAS_SABER junto a BITACORA · E. dogfood: registrar las citas causales de ESTA corrida con el ref propio (prueba viva RED→GREEN conductual) · F. test estructural (extiende test-saber.sh)"
nota_release: "re-sello + tag DIFERIDOS al próximo forjar-release.sh del operador."
---

Corrida abierta bajo goal 'dejar funcional'. Colaboración cross-sesión con la
sesión de RAG (que midió el problema). Plan del líder (con supuestos, ADR 0025)
→ Steward fresco (opus) → Ingeniero (opus) → roster fresco (opus) → dogfood de
la cita causal sobre el propio cierre → cierre en dos commits + sello.

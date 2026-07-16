---
id: 2026-07-16-escalera-diagnostico-microfix
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "v2.1.0 — escalera T1: skills diagnostico (peldaño 0) + microfix (peldaño 1) + cableado"
tier: "completo (toca registros.yaml y adoptar-crisol.sh + establece el patrón escalera en la ley)"
target: "pc-local (Git-Bash del operador — forja la familia de skills; directiva de sesión del operador, debate 2026-07-16)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.0.0 (verificada contra remoto tras el release)"
iteraciones: "3/3"
runState: wip
veredictos: []
refs: [adr:0017, adr:0016, corrida:2026-07-16-refactor-arbol-registros]
---
- ORIGEN: el operador aclaró que el goal del play cubría TODO el diseño aprobado del debate, no solo el cimiento — el backlog aprobado (docs/IDEAS.md + ADR 0016 §Consecuencias) se ejecuta en tranches T1..T4, corridas chicas encadenadas.
- Alcance: [T1a] skill nueva `diagnostico` — peldaño 0 de la escalera, evaluador PASIVO read-only: reproduce, localiza (bitácora por síntoma + arquitectura por capa), hipotetiza, emite fila con zona sospechada + escalón/tope recomendado; invocable en CUALQUIER entorno (cero escritura al sistema observado). [T1b] skill nueva `microfix` — peldaño 1: sonda de UN comportamiento en UN punto; pregunta el tope si no viene indicado; TARGET obligatorio (env legal varía por peldaño/caso); veredicto favorable/no-favorable; escala a hotfix SIN saltos llevándose refs; en Fase 1 abre corrida fast-path mínima para satisfacer el gate (puente documentado; el peldaño propio del gate llega con Fase 2). [T1c] cableado en skill hotfix (peldaño 2: recibe refs del microfix). [T1d] tablas `diagnostico` y `microfix` en registros.yaml + siembra lazy en adoptar-crisol.sh. Sin cambios de comportamiento en skills existentes salvo el cableado aditivo.
- MIGRATION_STRATEGY: N/A (DDL solo aditivo en registros.yaml: 2 tablas lazy sin datos, trivialmente reversible por commit; sin DDL destructivo)
- ITER-2: FAIL de CREDITO del scope-verifier (iter 1) → depositado ADR 0017 "Escalera de calidad: peldaños 0-3" (entrada default, tope preguntado, sin saltos + excepción 1→3, TARGET por peldaño, puente de gate Fase 1→2, tablas) + esta línea de MIGRATION_STRATEGY reescrita por su observación menor. Re-verificación fresca: CREDITO PASS.
- ITER-3: FAIL de TEST_COVERAGE del quality-auditor (hallazgo PRE-EXISTENTE de v2.0.0, no regresión: el ledger sembrado por la adopción no llevaba marcador GENERADO → lint exit 1 en repo recién adoptado) → adoptar-crisol.sh proyecta el ledger SOLO cuando esta corrida lo sembró (jamás pisa un legacy — eso es /migrar); sandbox re-probado: toy lint exit 0. + nit del re-verificador: las 3 skills apuntan ahora a ADR 0017.

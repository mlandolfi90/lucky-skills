---
id: 2026-07-16-escalera-diagnostico-microfix
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "v2.1.0 — escalera T1: skills diagnostico (peldaño 0) + microfix (peldaño 1) + cableado"
tier: "completo (toca registros.yaml y adoptar-crisol.sh + establece el patrón escalera en la ley)"
target: "pc-local (Git-Bash del operador — forja la familia de skills; directiva de sesión del operador, debate 2026-07-16)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.0.0 (verificada contra remoto tras el release)"
iteraciones: "3/3"
runState: closing
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local, directiva de sesión del operador"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "iter1: enforcer 110-0 · paridad 10-0 · lint 0 · drift 0 · forja-dry v2.1.0 exit 0; iter3: regresión re-corrida 110-0 y 10-0"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-iter3, evidencia: "sandbox nuevo lint verde día 0 + 2da adopción no-op sha256 idéntico + ledger legacy INTACTO byte a byte + regresión completa"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "4 verificadores frescos iter1 + 2 re-verificadores frescos iter2/3"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "9 archivos del diff mapean 1:1 a T1a..T1d; fidelidad a la espec verificada punto por punto"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier-iter2, evidencia: "FAIL iter1 → ADR 0017 deposita las 6 normas de la escalera; frontmatter y refs válidos; INDEX regenerado"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "agente localizador + Fase 2 + T2..T4 con hogar declarado"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "DDL solo aditivo (2 tablas lazy sin datos, reversible)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0 + 9 archivos y 3 commits a mano: cero secretos/paths-con-usuario"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "282+/1− todo por agregado; única deleción = proyección regenerada; hotfix ganó sección aditiva sin tocar flujo"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "troncos nuevos 97/102 líneas; hotfix 279; fronteras entre peldaños mecánicas (regla del segundo lugar)"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "peldaño futuro = carpeta+tabla+heredoc, forja auto-enumera; puente de gate marcado transitorio con muerte en Fase 2"}
  - {regla: LISKOV, veredicto: N/A, quien: design-verifier, evidencia: "sin jerarquía de subtipos; contrato fila (columnas obligatorias) cumplido por ambos schemas"}
  - {regla: INTERFACE_SEGREGATION, veredicto: PASS, quien: design-verifier, evidencia: "tools por rol: diagnostico SIN Write/Edit (peldaño pasivo); microfix con ellas (su rol es tocar)"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: design-verifier, evidencia: "única edición a estable = sección aditiva en hotfix, declarada en el plan y sancionada por ADR 0017"}
  - {regla: CONFORMIDAD, veredicto: N/A, quien: líder, evidencia: "sin código hexagonal en el diff — trigger no aplica"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "TARGET local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 3/3 — dentro del techo, sin ESCALATED"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: gate, evidencia: "sin dependencias nuevas en T1"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "pre-flight 30 archivos con 1 ancla (incluye 2 skills nuevas + ADR 0017); re-sello uniforme a v2.1.0"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.1.0 exit 0 completo"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "tag anotado v2.1.0 tras CLOSED + matriz verde"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "cierre tras matriz completa verde (2 FAIL corregidos y re-verificados por frescos)"}
  - {regla: BUMP_REASON, veredicto: "N/A", quien: gate, evidencia: "sin bump de pins"}
refs: [adr:0017, adr:0016, corrida:2026-07-16-refactor-arbol-registros]
cierre: "2026-07-16 · commit de cierre + tag anotado v2.1.0 + GitHub Release"
---
- ORIGEN: el operador aclaró que el goal del play cubría TODO el diseño aprobado del debate, no solo el cimiento — el backlog aprobado (docs/IDEAS.md + ADR 0016 §Consecuencias) se ejecuta en tranches T1..T4, corridas chicas encadenadas.
- Alcance: [T1a] skill nueva `diagnostico` — peldaño 0 de la escalera, evaluador PASIVO read-only: reproduce, localiza (bitácora por síntoma + arquitectura por capa), hipotetiza, emite fila con zona sospechada + escalón/tope recomendado; invocable en CUALQUIER entorno (cero escritura al sistema observado). [T1b] skill nueva `microfix` — peldaño 1: sonda de UN comportamiento en UN punto; pregunta el tope si no viene indicado; TARGET obligatorio (env legal varía por peldaño/caso); veredicto favorable/no-favorable; escala a hotfix SIN saltos llevándose refs; en Fase 1 abre corrida fast-path mínima para satisfacer el gate (puente documentado; el peldaño propio del gate llega con Fase 2). [T1c] cableado en skill hotfix (peldaño 2: recibe refs del microfix). [T1d] tablas `diagnostico` y `microfix` en registros.yaml + siembra lazy en adoptar-crisol.sh. Sin cambios de comportamiento en skills existentes salvo el cableado aditivo.
- MIGRATION_STRATEGY: N/A (DDL solo aditivo en registros.yaml: 2 tablas lazy sin datos, trivialmente reversible por commit; sin DDL destructivo)
- ITER-2: FAIL de CREDITO del scope-verifier (iter 1) → depositado ADR 0017 "Escalera de calidad: peldaños 0-3" (entrada default, tope preguntado, sin saltos + excepción 1→3, TARGET por peldaño, puente de gate Fase 1→2, tablas) + esta línea de MIGRATION_STRATEGY reescrita por su observación menor. Re-verificación fresca: CREDITO PASS.
- ITER-3: FAIL de TEST_COVERAGE del quality-auditor (hallazgo PRE-EXISTENTE de v2.0.0, no regresión: el ledger sembrado por la adopción no llevaba marcador GENERADO → lint exit 1 en repo recién adoptado) → adoptar-crisol.sh proyecta el ledger SOLO cuando esta corrida lo sembró (jamás pisa un legacy — eso es /migrar); sandbox re-probado: toy lint exit 0. + nit del re-verificador: las 3 skills apuntan ahora a ADR 0017.
- RETRO: las 3 iteraciones se gastaron en artefactos de PROCESO (ADR faltante, siembra sin proyectar), no en las skills — el Planificador debería traer checklist de crédito + ensayo de adopción ANTES del roster; y el FAIL pre-existente demuestra que el roster fresco audita el terreno completo, no solo el diff (valioso: lo caza el primero que pasa).

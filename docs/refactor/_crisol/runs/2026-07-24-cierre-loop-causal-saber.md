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
iteraciones: "2/3 (iter1: roster fresco 4/4 PASS sobre el mecanismo base; iter2: delta-verify PASS del contrato lockeado por las 3 sesiones — la coordinación cross-sesión surfaceó lo que iter1 no tenía)"
runState: closing
cierre: "2026-07-24 · commits b1db1df (apertura) + a0ce2b3/dfd5896 (plan+enmienda) + ac64fe8 (iter1 mecanismo) + eb4f47b (iter2 contrato lockeado) + cierre en dos commits. Re-sello/tag DIFERIDOS al operador (publicar la ley es su acto)."
citas_saber: "N/A — esta corrida SHIPEA el mecanismo; NO disparó saber_telemetria (fuera de lane, ADR 0027 §Consecuencias). Fichas que el roster aplicó y serían citables por el lane saberes: FALSO-VERDE-004, DRIFT-007 (el firing en vivo es del canal RAG↔Hackaton)."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: quality-auditor-2, evidencia: "pc-local (el qa2 verificó AHÍ, intérprete sondado python real no stub)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus en steward/ingenieros/roster; líder opus-4.8 (el operador cambió de modelo mid-corrida) — goal 'dejar funcional'"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "iter1: bloque CITAS_SABER se INSERTA sin reescribir BITACORA (crisol:517); iter2: el lint es check #8 nuevo sin tocar 1-7 (registros-lint:383-393). Adición pura; ADR 0027 nuevo"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "una responsabilidad por unidad: ADR=decisión, /saber citar=el cómo, campo=enganche, lint=guardia. Split 'una define, otra apunta' DRY"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "espejo del mecanismo BITACORA/destilación (probado); REFUERZO se AGREGA junto a CAPTURA. Nada se borra → DESAPARECE (ADR 0024) NO aplica, confirmado"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "el único edit a estable (§4 paso 8) es extensión acreditada por ADR 0027; el resto AGREGA"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0027 ACEPTADA, frontmatter válido, refs recíprocas corrida↔ADR; INDEX regenerado"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "iter1+iter2: mapa a actos A/B/C/D/F/G; acto E (firing en vivo) fuera de alcance por límite del operador; CERO llamada saber_* y CERO escritura al repo saberes, verificado por grep del diff en ambas iteraciones"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "diferidos declarados: firing en vivo + promoción CANDIDATE→LIVE = lane saberes (RAG↔Hackaton); rastro server-side por sesión = lane saberes; re-sello/tag = operador"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor-2, evidencia: "iter1: 17/17 suites + 2 gates exit 0 en pc-local; iter2: test-saber 12/12 + registros-lint 0 + el lint nuevo probado en 4 sub-casos (reporta CLOSED≥2026-07-24 sin campo, N/A satisface, no-retroactivo <2026-07-24, limpio al borrar temp)"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-2, evidencia: "test-saber suma A7-A11 (10→12 PASS); la corrida AGREGA cobertura estructural del mecanismo + del lint"}
  - {regla: RED_GREEN, veredicto: PASS, quien: lider, evidencia: "iter1: 3 asserts vistos en rojo antes de B/C/D; iter2: A10/A11 en rojo (10→12) + el lint en rojo con un temp CLOSED 2026-07-24 sin campo → verde al agregar N/A y al borrar el temp"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "iter1 leak-scan exit 0 + iter2 delta leak-scan exit 0; cero secretos (la única mención de dominio es el slug del propio repo)"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "sin deps; test-pin-scan corrido por él 3/3, árbol sin floating"}
  - {regla: LISKOV, veredicto: "N/A", quien: design-verifier, evidencia: "prosa normativa, sin implementación de abstracción"}
  - {regla: INTERFACE_SEGREGATION, veredicto: "N/A", quien: design-verifier, evidencia: "sin contrato multi-cliente nuevo"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras roster 4/4 (iter1) + delta-verify (iter2) verdes"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no toca UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no toca código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "no habilita release; sellos v2.9.0 intactos (verificado)"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "no se crea tag en esta corrida"}
retro: "El valor real fue la coordinación de las 3 sesiones: la iter1 shipeó un mecanismo sólido (roster 4/4) que HABRÍA nacido roto en producción — Hackaton, leyendo la fuente (telemetry.py:28), cazó que el regex del ref rebota espacios/em-dash con InputError SILENCIOSO, la causa raíz probable del 49/50 en cero que RAG midió. La iter2 lo corrigió (ref=slug-id) + ancló al dedup_key (sobrevive el rename CAND→GAP que huérfana citas) + adoptó el lint no-retroactivo (RAG lo pidió; el operador movió a auto-promoción que LEE esta señal). El límite del operador ('lo de saberes es del canal RAG↔Hackaton') se respetó al pie en las 2 iteraciones: cero escritura al saber, verificado por grep en ambas. Fricción menor: la convención del ref cambió entre iter1 (ruta) e iter2 (slug) — una decisión de contrato que solo el diálogo cross-sesión podía cerrar bien; sola, la iter1 la habría clavado mal."
bitacora: "N/A (sin disparador nuevo destilable propio: el hallazgo del regex-silencioso es de Hackaton y ya es ficha de ELLA en el saber; el de credenciales es GAP-001/CAND-9b928849d1ea, de RAG. Esta corrida CONSUMIÓ esas lecciones, no las generó)."
origen: "encargo cross-sesión de 'Evaluación de arquitecturas RAG (fork 2)', endosado por el operador (goal 'dejar funcional'). Problema MEDIDO por esa sesión con saber_metricas (2026-07-24): de ~50 fichas, las consultas fluyen (DRIFT-004/FALSO-VERDE-004 con 16, DRIFT-001 con 13) pero las citas causales están en 0 salvo DRIFT-001 (2). El loop consulta→refuerzo no cierra: saber_telemetria existe y nadie lo llama."
alcance: "A. ADR 0027 (decisión: el cierre registra SIEMPRE las citas causales, espejo de BITACORA/destilación — CAPTURA ya cableada, REFUERZO no) · B. saber/SKILL.md subcomando nuevo /saber citar (define el cómo: fichas consultadas en la sesión → endoso humano de cuáles funcionaron → saber_telemetria con el run_ledger_ref) · C. crisol/SKILL.md §4 paso 8 puntero + campo CITAS_SABER registrado siempre (citas o N/A) · D. template run-ledger.md agrega CITAS_SABER junto a BITACORA · E. dogfood: registrar las citas causales de ESTA corrida con el ref propio (prueba viva RED→GREEN conductual) · F. test estructural (extiende test-saber.sh)"
nota_release: "re-sello + tag DIFERIDOS al próximo forjar-release.sh del operador."
---

Corrida abierta bajo goal 'dejar funcional'. Colaboración cross-sesión con la
sesión de RAG (que midió el problema). Plan del líder (con supuestos, ADR 0025)
→ Steward fresco (opus) → Ingeniero (opus) → roster fresco (opus) → dogfood de
la cita causal sobre el propio cierre → cierre en dos commits + sello.

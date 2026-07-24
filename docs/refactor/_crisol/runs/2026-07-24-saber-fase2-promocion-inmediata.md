---
id: 2026-07-24-saber-fase2-promocion-inmediata
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-24
branch: main
titulo: "Saber Fase 2 — promoción inmediata (captura→LIVE); el juicio humano se MUEVE a curaduría-posterior (/saber destilar); deroga 'contar ≠ ungir' y 'promoción la endosa el humano'"
tier: "completo (DEROGA un invariante central de la ley — endoso humano por-ficha pre-LIVE; ADR de cambio de invariante; toca saber/SKILL.md + posiblemente crisol/bitacora; norma nueva transversal)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder opus-4.8 + subagentes) — goal 'terminar sin intervención'; GO DIRECTO del operador ('dale gooo', 2026-07-24)"
ley: "v2.10.2 (sello local == último tag)"
iteraciones: "1/3 (Steward APPROVE 1ª + 4 correcciones inline aplicadas; roster fresco 4/4 PASS 1ª; una incoherencia intra-archivo de bitacora reconciliada post-roster antes de cerrar)"
runState: closing
refs: [adr:0028, adr:0023, adr:0027, adr:0015, adr:0024]
cierre: "2026-07-24 · commits apertura + plan + Steward-inline + rewrite (b60b873) + coherencia bitacora (8f64c23) + cierre en dos commits. Forja v2.11.0 habilitada (GO directo del operador + pin de Hackaton, ambos cumplidos)."
citas_saber: "N/A — corrida de LEY (no de código de app); el roster aplicó FALSO-VERDE-004/DRIFT-007 al verificar (citables por el lane saberes bajo el contrato nuevo, no desde acá)."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: quality-auditor-2, evidencia: "pc-local (verificó AHÍ, intérprete python sondado)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus en steward/ingeniero/roster; líder opus-4.8; GO directo del operador"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "edit a estable bajo ADR 0028 (cambio de invariante); 0028 deroga POR-PUNTO vía refs (supersede:null), 0023/0027/0015 byte-intactos (git diff vacío)"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "/saber destilar (curaduría) invoca /saber podar (única garganta), no reimplementa; destilador sigue capturador read-only"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "renombre /saber destilar→capturar coherente (crisol §4 apunta al nuevo); curaduría se apoya en tools del server sin duplicar; DESAPARECE (los 5 modos) verificado como eliminación real por diff de resta"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "el edit a estable (saber/crisol/bitacora) tiene caso legal nominado = ADR 0028"}
  - {regla: PRINCIPIO_CONSERVADO, veredicto: PASS, quien: design-verifier, evidencia: "'el humano decide qué es verdad' CONSERVADO (movido a curaduría, no vaciado; saber:27/203, ADR 0028 §Conservado) — no es tergiversación del endoso"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0028 ACEPTADA, frontmatter válido, 0028→0023/0027/0015/0024 en refs; recíproca corrida→0028 foldeada en este cierre; INDEX regenerado"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "mapa 1:1 a los actos; CERO firing de tool saber_* (solo prosa) y CERO escritura al repo saberes (verificado); residuales tier-1 parkeados en IDEAS"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "4 residuales stale tier-1 (hook + 3 punteros) parkeados como follow-up en IDEAS.md; la incoherencia intra-archivo tier-2 de bitacora se RECONCILIÓ (no se parkeó)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor-2, evidencia: "17/17 suites exit 0 en pc-local + registros-lint 0 + proyectar --check byte-idéntico"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor-2, evidencia: "test-saber 14/14: A12 (regla de fusión de RAG) + A13 (/saber capturar) nuevos"}
  - {regla: RED_GREEN, veredicto: PASS, quien: lider, evidencia: "A12/A13 vistos fallar antes del rewrite (12→14 PASS, reportado por el ingeniero)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0 + barrido manual del diff completo: 0 hallazgos"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "sin deps nuevas; test-pin-scan corrido por él 3/0, árbol sin floating"}
  - {regla: LISKOV, veredicto: "N/A", quien: design-verifier, evidencia: "prosa normativa"}
  - {regla: INTERFACE_SEGREGATION, veredicto: "N/A", quien: design-verifier, evidencia: "sin contrato multi-cliente nuevo"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras roster 4/4 + coherencia reconciliada"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL; la migración de CANDIDATE-legacy es server-side (lane Hackaton)"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "re-sello en la forja v2.11.0"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "tag en la forja"}
retro: "El cambio más grande de la ley (deroga el invariante más enfático del operador) salió limpio por la disciplina, no por suerte. (1) FASE PIN aplicada al pie: NO hice la ingeniería hasta que Hackaton CERRÓ su server y pineó el contrato — la lección forjar-tras-contrato-de-sesion-dependiente, un nivel más profundo. (2) El norte 'el humano decide qué es verdad se MUEVE, no muere' mantuvo el cambio coherente con la ley del operador, no en su contra — el design-verifier lo confirmó. (3) El fresh-eyes gate volvió a ganarse el sueldo: el scope-verifier cazó una incoherencia intra-archivo de bitacora que el ingeniero dejó (3 líneas del modelo viejo contradiciendo lo que el mismo archivo ahora enseña); al reconciliarla, YO cacé una cuarta (:238) que el verificador no vio. Ninguno solo la veía entera. (4) La supersesión por refs (viejos byte-intactos) respetó la inmutabilidad de los registros (ADR 0016) mientras derogaba puntos vía ADR 0028."
bitacora: "N/A (sin disparador destilable propio: el modelo nuevo lo diseñó Hackaton en el server; esta corrida cableó la doctrina en lucky-skills consumiendo ese contrato)."
origen: "GO DIRECTO del operador en su chat (2026-07-24, 'dale gooo'), tras surface explícito por mí Y por el hub SalaDeChat de que el cambio DEROGA su invariante más enfático (endoso humano ficha-por-ficha). NO se ejecutó por relay: el operador lo autorizó él mismo, entendiendo las tensiones. Reframe del modelo del saber (decidido hoy): endoso INMEDIATO sin umbral (captura→LIVE directo), la cita causal pasa a ser HISTORIAL de cómo/cuándo funcionó, y la DESTILACIÓN (batch, humana) reemplaza al endoso por-ficha como el acto de juicio humano — que se mueve de pre-LIVE a curaduría-posterior."
alcance: "PENDIENTE de arqueología + plan (FASE PIN). Preliminar: (1) ADR de cambio de invariante — deroga 'contar ≠ ungir' y 'CANDIDATE→LIVE solo por acto humano', con el porqué del operador y el ENCUADRE de que el juicio humano se MUEVE (no se elimina) a la destilación; (2) /saber destilar como ritual humano de curaduría (consolidar batch + historiales, forjar el canónico, podar evidencia-cero tras ventana ~30d con retiro reversible=archivar) — EXTENDER la infra de destilación existente, no duplicar; (3) actualizar los subcomandos afectados de saber (promover/revisar) y la doctrina de endoso; (4) CHANGELOG + bump v2.11.0. Diseño de RAG registrado: núcleo = fusión de cuasi-duplicados semánticos; cadencia/gatillo barato (sugerido al cierre de corrida o por umbral)."
desaparece: "estado CANDIDATE (fichas) · /saber promover (paso de ciclo) · /saber revisar (puerta de entrada al catálogo) · gate 'PROHIBIDO BATCH' pre-LIVE · flujo mcp-inbox para fichas — declarado para el design-verifier (ADR 0024): es ELIMINACIÓN de modos, no reubicación"
nota_release: "NO forjar hasta (1) [HECHO] palabra directa del operador Y (2) [HECHO] pin del contrato del server de Hackaton (CLOSED, commit 77f6138). Ambas cumplidas → forja v2.11.0 habilitada al cierre. Un solo release."
---

Fase 2 bajo GO directo del operador. Norte: el juicio humano NO se elimina — se MUEVE de
gate-pre-LIVE a curaduría-posterior (destilación). Arqueología (mapear los invariantes que
se derogan + la infra de destilación a extender) → plan con supuestos → Steward → Ingeniero
→ roster → cierre. Forja DIFERIDA al pin del server de Hackaton.

---
id: 2026-07-24-loop-causal-content-key
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-24
branch: main
titulo: "Corrección del anchor de /saber citar: pasar entry_id, el server resuelve a content_key (el dedup_key NO existe a nivel de ficha)"
tier: "fast-path (corrección de prosa en 1 skill + nota de ADR + 1 assert de test; sin código nuevo, sin contrato de matriz)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder opus-4.8 + verificación) — goal 'terminar sin intervención + documentar los porqué'"
ley: "v2.10.0 (sello local == último tag)"
iteraciones: "2/3 (iter1 FAIL: el verificador fresco cazó que el ADR §Decisión punto 3 seguía diciendo 'anclá al dedup_key' mientras §Consecuencias ya decía 'pasá entry_id' — ADR auto-contradictorio; iter2: corregido §Decisión punto 3, re-verificado fresco PASS)"
runState: closed
cierre: "2026-07-24 · fast-path 2/3; verificador fresco FAIL→fix→PASS. Habilita forja v2.10.1."
citas_saber: "N/A — corrección de prosa; no se consultó ni citó ninguna ficha del saber."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: lider, evidencia: "pc-local (directiva durable)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus-4.8 líder + verificadores"}
  - {regla: REGLA0, veredicto: PASS, quien: verificador, evidencia: "test-saber 12/12 + registros-lint 0, corridos por el verificador en pc-local; A10 ahora chequea content_key"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: verificador, evidencia: "test-saber sigue 12/12; A10 actualizado al contrato correcto (content_key)"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: verificador, evidencia: "corrección de prosa acotada (saber §/saber citar paso 3-5 + ADR 0027 §Decisión pto3/§Consecuencias + assert A10); sello v2.10.0 intacto"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: verificador, evidencia: "solo saber/SKILL.md + ADR 0027 + test-saber (declarados); cero llamada saber_*, cero escritura al repo saberes"}
  - {regla: FIDELIDAD, veredicto: PASS, quien: verificador, evidencia: "iter2: ADR↔skill dicen el MISMO contrato (pasá entry_id → server resuelve a content_key → coalesce rename); dedup_key solo en 'por qué NO'. iter1 había FALLADO acá"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: verificador, evidencia: "leak-scan exit 0; cero secretos"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras re-verificación PASS"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "el operador forja v2.10.1 aparte"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "no crea tag en esta corrida"}
retro: "Doble lección. (1) El fresh-eyes gate probó su valor OTRA VEZ: el verificador cazó que corregí §Consecuencias del ADR pero dejé §Decisión punto 3 diciendo lo contrario — el líder solo NO lo veía (había limitado el alcance del edit a §Consecuencias). iter1 FAIL honesto → iter2 fix → PASS. (2) La causa de fondo: forjé v2.10.0 apenas el operador dijo 'terminar', pero Hackaton había pedido esperar su contrato final del server (el dedup_key resultó no existir; el ancla real es content_key resuelto server-side desde el entry_id). Forjar antes del contrato final causó esta re-forja. Lección: cuando otra sesión está cerrando el contrato del que dependés, su cierre pesa más que 'forjar rápido' — el goal 'terminar' no significa 'terminar antes que la dependencia'."
bitacora: "N/A (el hallazgo del contrato es de Hackaton en el saber; esta corrida lo consumió)."
origen: "corrección load-bearing de Hackaton (3 lecturas independientes del código: RAG + su Planificador + su Steward): el `dedup_key` NO se persiste en la ficha ni lo sirve saber_ficha — es el kebab que se pasa al PROPONER, nada más. El único id estable real es el CONTENT_KEY del server (sha256(síntoma·\\x00·acción)[:12], recomputable al servir, sobrevive el rename CAND→GAP porque la promoción no toca síntoma/acción). El contrato correcto y MÁS SIMPLE: /saber citar pasa el entry_id (el id-display GAP-nnn/CAND-xxx) y el SERVER lo resuelve internamente a content_key y coalesce las citas — el consumidor no maneja ninguna clave estable. La skill v2.10.0 nombra dedup_key (inexacto); esta corrida lo corrige antes de que RAG dispare la primera cita real."
alcance: "(a) saber/SKILL.md §/saber citar paso 3: reemplazar 'anclá al dedup_key' por 'pasá el entry_id, el server resuelve a content_key y coalesce el rename'; el ref estable para auditar en CITAS_SABER = el content_key que Hackaton expondrá vía saber_ficha (hasta entonces el entry_id); event_id = cita:<corrida-slug>:<entry_id>; sesion = session_id del cliente MCP. (b) docs/decisions/0027 §Consecuencias: corregir la nota de deuda (content_key, no dedup_key; el desacople pasa-entry_id). (c) test-saber A10: chequear 'content_key' en vez de 'dedup_key'. Contrato sigue FLEXIBLE (el field exacto donde saber_ficha expone content_key lo pinea un micro-update cuando la corrida server cierre)."
nota_release: "habilita forja v2.10.1 (micro, goal 'terminar sin intervención'). RETRO: forjar v2.10.0 antes del contrato final de Hackaton causó esta re-forja — la skill quedó flexible (no rompió) pero nombraba la clave equivocada."
---

Fast-path bajo goal 'terminar sin intervención'. Corrige el anchor nombrado (dedup_key
inexistente → pasar entry_id, el server resuelve a content_key), antes de que RAG dispare
la primera cita real. Verificación: REGLA 0 (test-saber) + leak + verificador fresco del delta.

---
id: 2026-07-24-loop-causal-content-key
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-24
branch: main
titulo: "Corrección del anchor de /saber citar: pasar entry_id, el server resuelve a content_key (el dedup_key NO existe a nivel de ficha)"
tier: "fast-path (corrección de prosa en 1 skill + nota de ADR + 1 assert de test; sin código nuevo, sin contrato de matriz)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder opus-4.8 + verificación) — goal 'terminar sin intervención + documentar los porqué'"
ley: "v2.10.0 (sello local == último tag)"
iteraciones: "1/3"
runState: wip
origen: "corrección load-bearing de Hackaton (3 lecturas independientes del código: RAG + su Planificador + su Steward): el `dedup_key` NO se persiste en la ficha ni lo sirve saber_ficha — es el kebab que se pasa al PROPONER, nada más. El único id estable real es el CONTENT_KEY del server (sha256(síntoma·\\x00·acción)[:12], recomputable al servir, sobrevive el rename CAND→GAP porque la promoción no toca síntoma/acción). El contrato correcto y MÁS SIMPLE: /saber citar pasa el entry_id (el id-display GAP-nnn/CAND-xxx) y el SERVER lo resuelve internamente a content_key y coalesce las citas — el consumidor no maneja ninguna clave estable. La skill v2.10.0 nombra dedup_key (inexacto); esta corrida lo corrige antes de que RAG dispare la primera cita real."
alcance: "(a) saber/SKILL.md §/saber citar paso 3: reemplazar 'anclá al dedup_key' por 'pasá el entry_id, el server resuelve a content_key y coalesce el rename'; el ref estable para auditar en CITAS_SABER = el content_key que Hackaton expondrá vía saber_ficha (hasta entonces el entry_id); event_id = cita:<corrida-slug>:<entry_id>; sesion = session_id del cliente MCP. (b) docs/decisions/0027 §Consecuencias: corregir la nota de deuda (content_key, no dedup_key; el desacople pasa-entry_id). (c) test-saber A10: chequear 'content_key' en vez de 'dedup_key'. Contrato sigue FLEXIBLE (el field exacto donde saber_ficha expone content_key lo pinea un micro-update cuando la corrida server cierre)."
nota_release: "habilita forja v2.10.1 (micro, goal 'terminar sin intervención'). RETRO: forjar v2.10.0 antes del contrato final de Hackaton causó esta re-forja — la skill quedó flexible (no rompió) pero nombraba la clave equivocada."
---

Fast-path bajo goal 'terminar sin intervención'. Corrige el anchor nombrado (dedup_key
inexistente → pasar entry_id, el server resuelve a content_key), antes de que RAG dispare
la primera cita real. Verificación: REGLA 0 (test-saber) + leak + verificador fresco del delta.

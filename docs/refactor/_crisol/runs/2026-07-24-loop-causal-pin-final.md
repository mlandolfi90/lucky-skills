---
id: 2026-07-24-loop-causal-pin-final
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-24
branch: main
titulo: "Pin final del contrato del loop causal: saber_ficha NO expone content_key (server resuelve entry_id internamente); sesion = param 'sesion' = mcp-session-id — deuda de ADR 0027 CERRADA"
tier: "fast-path (pin de prosa en 1 skill + cierre de la nota de deuda del ADR; sin código nuevo, sin contrato de matriz)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder opus-4.8 + verificación) — goal 'terminar sin intervención + documentar los porqué'"
ley: "v2.10.1 (sello local == último tag)"
iteraciones: "1/3"
runState: wip
origen: "Skills Hackaton CERRÓ su corrida server (lucky-tool-saber CLOSED, deploy f864b1d live, e2e VERDE: metrics(GAP-024)=11=metrics(CAND-af1f29893a9a) — las 10 consultas varadas bajo el id muerto coalescieron bajo el promovido). Shapes finales: (1) saber_ficha NO expone content_key — quedó fuera de scope y NO hace falta: el server resuelve el entry_id→content_key (content_key_for) internamente antes de record_causal; el consumidor SIEMPRE pasa el entry_id y nunca maneja clave estable. (2) el param se llama `sesion` (en saber_buscar/saber_ficha/saber_telemetria), valor = session_id del cliente MCP, mismo string consulta↔cita. Esta corrida PINEA ese contrato final y CIERRA la deuda declarada en ADR 0027 (la corrida server ya cerró — es el momento del pin único, no un refinamiento intermedio)."
alcance: "(a) saber/SKILL.md §/saber citar: reemplazar la línea stale del ref-de-auditoría ('cuando Hackaton exponga content_key vía saber_ficha') por el contrato final confirmado (saber_ficha NO lo expone ni hace falta; SIEMPRE pasás el entry_id, el server resuelve internamente; para auditar en CITAS_SABER registrás el entry_id); pinear el ejemplo de evento y el `sesion`. (b) docs/decisions/0027 §Consecuencias: CERRAR la nota de deuda (resuelta por la corrida server de Hackaton, con la evidencia e2e). Sin cambio de contrato de matriz."
nota_release: "habilita forja v2.10.2 (el PIN ÚNICO tras el cierre de la dependencia — coherente con la lección [[forjar-tras-contrato-de-sesion-dependiente]]). Cierra la deuda de ADR 0027. RAG ya probó el mecanismo vivo bajo v2.10.1 (2 citas 0→1); este pin es de precisión de contrato/doc, no de comportamiento."
---

Fast-path bajo goal 'terminar sin intervención'. Pin del contrato final tras el CIERRE
de la corrida server de Hackaton. Verificación: REGLA 0 (test-saber) + leak + verificador
fresco del delta.

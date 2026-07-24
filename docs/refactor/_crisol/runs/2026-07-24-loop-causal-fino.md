---
id: 2026-07-24-loop-causal-fino
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-24
branch: main
titulo: "Fino del loop causal: /saber citar no asume que saber_ficha expone dedup_key + sesion = session_id del cliente MCP"
tier: "fast-path (prosa aditiva/correctiva en 1 skill, saber/SKILL.md; sin código nuevo, sin contrato de matriz)"
target: "pc-local (la forja; directiva durable del operador para lucky-skills)"
model: "opus (líder opus-4.8 + verificación) — goal 'terminar sin intervención + documentar los porqué'"
ley: "v2.9.0 (sello local == último tag)"
iteraciones: "1/3"
runState: wip
origen: "corrección de contrato de Hackaton (leyó la fuente lucky-tool-saber): (1) saber_ficha HOY no expone el dedup_key — Entry no persiste ese campo — así que el paso '/saber citar hace saber_ficha(ID)→lee dedup_key' de la corrida cierre-loop-causal-saber NO funciona todavía; (2) el `sesion` no puede ser el slug de la corrida (las consultas pasan ANTES de que la corrida tenga id) → va el session_id del cliente MCP, estable toda la sesión. Ambas suposiciones quedaron mal en la corrida previa (CLOSED); esta las corrige ANTES de forjar para no shipear un skill roto."
alcance: "saber/SKILL.md §/saber citar: (a) NO afirmar que saber_ficha expone dedup_key hoy — anclar al 'id estable según el contrato del saber' (Hackaton lo expondrá vía saber_ficha + definirá el field-ancla en saber_telemetria; hasta entonces el consumidor no asume que ya está, y la limitación actual — telemetria toma entry_id que la promoción huérfana — se declara); (b) `sesion` = session_id del cliente MCP (estable toda la sesión), NO el slug de la corrida. Mantener el contrato FLEXIBLE/desacoplado: el ejemplo exacto se pinea cuando la corrida server de Hackaton aterrice."
nota_release: "esta corrida habilita la forja v2.10.0 (el operador la autorizó vía goal 'terminar sin mi intervención'); el pin del shape exacto (field id-estable + field sesion) es un micro-update futuro cuando Hackaton pase los dos shapes finales."
---

Fast-path bajo goal 'terminar sin intervención'. Corrige dos suposiciones de contrato
que Hackaton cazó leyendo la fuente, antes de forjar. Verificación: REGLA 0 (test-saber)
+ leak + un verificador fresco del delta.

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
runState: closing
cierre: "2026-07-24 · fast-path; verificador fresco PASS. Habilita la forja v2.10.0 (goal 'terminar sin intervención')."
citas_saber: "N/A — fast-path de corrección de prosa; no se consultó ni citó ninguna ficha del saber."
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: lider, evidencia: "pc-local (directiva durable)"}
  - {regla: MODEL, veredicto: PASS, quien: lider, evidencia: "opus-4.8 líder + verificador"}
  - {regla: REGLA0, veredicto: PASS, quien: verificador, evidencia: "test-saber 12/12 + registros-lint 0, corridos por él en pc-local; A10/A11 verdes tras la corrección"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: verificador, evidencia: "test-saber sigue 12/12; la corrección no baja cobertura"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: verificador, evidencia: "corrección de prosa acotada a §/saber citar paso 3 + bullet en ADR 0027 §Consecuencias; no reescribe; sello v2.9.0 intacto"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: verificador, evidencia: "solo saber/SKILL.md + ADR 0027 (declarados) + la fila; cero llamada saber_*, cero escritura al repo saberes"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: verificador, evidencia: "leak-scan exit 0 + revisión manual; cero secretos"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: gate, evidencia: "cierre tras verificador PASS"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: gate, evidencia: "no UI"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: gate, evidencia: "no código hexagonal"}
  - {regla: SELLOS, veredicto: "N/A", quien: gate, evidencia: "no habilita release por sí; el operador forja v2.10.0 aparte"}
  - {regla: TAG_GATE, veredicto: "N/A", quien: gate, evidencia: "no crea tag en esta corrida"}
retro: "Hackaton, leyendo la fuente del server, cazó DESPUÉS del cierre de la corrida madre que dos suposiciones del contrato estaban mal (saber_ficha no expone dedup_key hoy; sesion≠slug). Corregir en fast-path ANTES de forjar evitó shipear un skill roto a la flota — exactamente el falso-verde que el sistema combate. El valor cross-sesión otra vez: sola, la corrida madre habría forjado con dos instrucciones que fallan en runtime. La deuda de contrato quedó DECLARADA (ADR 0027 §Consecuencias): el pin del shape exacto es un micro-update cuando la corrida server aterrice."
bitacora: "N/A (sin disparador destilable propio: el hallazgo del contrato es de Hackaton en el saber; esta corrida lo CONSUMIÓ)."
origen: "corrección de contrato de Hackaton (leyó la fuente lucky-tool-saber): (1) saber_ficha HOY no expone el dedup_key — Entry no persiste ese campo — así que el paso '/saber citar hace saber_ficha(ID)→lee dedup_key' de la corrida cierre-loop-causal-saber NO funciona todavía; (2) el `sesion` no puede ser el slug de la corrida (las consultas pasan ANTES de que la corrida tenga id) → va el session_id del cliente MCP, estable toda la sesión. Ambas suposiciones quedaron mal en la corrida previa (CLOSED); esta las corrige ANTES de forjar para no shipear un skill roto."
alcance: "(a) saber/SKILL.md §/saber citar paso 3: NO afirmar que saber_ficha expone dedup_key hoy — anclar al 'id estable según el contrato del saber' (Hackaton lo expondrá vía saber_ficha + definirá el field-ancla en saber_telemetria; se declara la limitación actual: telemetria toma entry_id que la promoción huérfana); `sesion` = session_id del cliente MCP (estable toda la sesión), NO el slug de la corrida. (b) docs/decisions/0027 §Consecuencias: bullet de 'deuda de contrato declarada (pin pendiente)' con el mismo detalle, para que el registro de revisión sea fiel. Contrato FLEXIBLE/desacoplado: el ejemplo exacto se pinea cuando la corrida server de Hackaton aterrice."
nota_release: "esta corrida habilita la forja v2.10.0 (el operador la autorizó vía goal 'terminar sin mi intervención'); el pin del shape exacto (field id-estable + field sesion) es un micro-update futuro cuando Hackaton pase los dos shapes finales."
---

Fast-path bajo goal 'terminar sin intervención'. Corrige dos suposiciones de contrato
que Hackaton cazó leyendo la fuente, antes de forjar. Verificación: REGLA 0 (test-saber)
+ leak + un verificador fresco del delta.

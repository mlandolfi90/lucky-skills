---
id: 2026-07-16-ramas-agentes-canonicos
schema: corrida/1
tipo: corrida
estado: CLOSED
creado: 2026-07-16
branch: main
titulo: "v2.2.0 — T2: mecanismo de ramas con cuarentena + guardianes canónicos"
tier: "completo (toca proyectar.py/forja + establece los patrones rama y agente-canónico en la ley)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.1.0 (recién forjada y publicada en esta sesión)"
iteraciones: "2/3"
cierre: "2026-07-16 · commit de cierre + tag anotado v2.2.0 + GitHub Release"
runState: closing
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local, directiva de sesión"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "enforcer 110-0 · paridad 10-0 · ramas 8-0 · atomicidad 8-0 · lints 0 · forja-dry v2.2.0 exit 0"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "4 suites + 2 lints + forja dry + verificación funcional (bloque/fuente-única/frontmatter de agentes)"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "4 frescos iter-1 + 1 re-verificador fresco iter-2; roster spawneado desde definiciones canónicas"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "mapeo archivo→ítem T2a..T2e 1:1; sellado de ramas endosado en ITER-2"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier-iter2, evidencia: "ADR 0018 al ABRIR; reciprocidad fila↔ADR restaurada en iter-2"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "deuda hash-agents con doble hogar; telemetría→T3 con captura viva"}
  - {regla: MIGRATION, veredicto: N/A, quien: gate, evidencia: "sin DDL"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan exit 0 + 16 archivos y 3 commits a mano + grep dirigido: 0 hallazgos reales"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "todo agregado; ediciones a estables = casos legales decretados por ADR 0018 depositado al abrir"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "proyectar.py 254L una responsabilidad (el bloque RAMAS ES proyección); >400 resuelto por nombre; sin duplicación tronco↔rama"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "rama futura = archivo y nada más (glob+find genéricos); default canal=propuesta = cuarentena fail-closed"}
  - {regla: LISKOV, veredicto: PASS, quien: design-verifier, evidencia: "rama 001 sustituto fiel del texto del tronco; 6 agentes sustitutos fieles de los prompts del líder (contrato de output idéntico) — prueba viva: esta corrida los usó"}
  - {regla: INTERFACE_SEGREGATION, veredicto: PASS, quien: design-verifier, evidencia: "6/6 agentes con tools mínimas (sin Write/Edit); delega:[] sin anidar"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: design-verifier, evidencia: "cada edición a estable citada a su § del ADR 0018"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "cero deps nuevas; footers pinean v2.1.0→bump por forja"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas — trigger no aplica"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: TECHO_ITER, veredicto: PASS, quien: líder, evidencia: "convergió en 2/3"}
  - {regla: FIDELIDAD_ESPEC, veredicto: PASS, quien: scope-verifier-iter2, evidencia: "excepción one-time-scaffold con números verificados (589→591; normativo −12; pendiente decreciente demostrada)"}
  - {regla: SELLOS, veredicto: PASS, quien: forja, evidencia: "pre-flight 40 archivos 1 ancla (6 agents + 2 ramas incluidos); re-sello uniforme v2.2.0"}
  - {regla: FORJA, veredicto: PASS, quien: forja, evidencia: "forjar-release.sh v2.2.0 exit 0"}
  - {regla: TAG_GATE, veredicto: PASS, quien: líder, evidencia: "tag anotado v2.2.0 tras CLOSED + matriz verde"}
  - {regla: CIERRE_TRAS_PASS, veredicto: PASS, quien: líder, evidencia: "cierre tras roster verde + re-verificación fresca"}
  - {regla: BUMP_REASON, veredicto: "N/A", quien: gate, evidencia: "sin bump de pins"}
refs: [adr:0018, adr:0016, adr:0017, corrida:2026-07-16-escalera-diagnostico-microfix]
---
- ORIGEN: tranche T2 del backlog aprobado (debate 2026-07-16); lección del RETRO de T1 aplicada: el ADR de patrón se deposita AL ABRIR, no tras un FAIL.
- Alcance: [T2a] ADR 0018 (el árbol vivo: ramas + cuarentena + guardianes canónicos). [T2b] mecanismo de RAMAS en proyectar.py — bloque <!-- RAMAS:BEGIN/END --> del tronco regenerado desde <skill>/ramas/*.md (patrón blockinfile); SOLO ramas canal:estable y estado LIVE/EN_DUDA entran al índice (cuarentena: canal:propuesta NO rutea hasta endoso del operador); lint extendido (ramas sin bloque en el tronco = hallazgo). [T2c] test-ramas.sh (indexado, cuarentena, idempotencia, drift). [T2d] primera rama real: crisol/ramas/001-builds-de-imagen-ci.md — extrae del tronco la regla condicional "builds de imagen: gate-test horneado en CI" (gatillo: el artefacto es una imagen) — el tronco ADELGAZA y estrena el mecanismo. [T2e] guardianes canónicos en plugins/lucky/agents/ (quality-auditor, design-verifier, leak-verifier, scope-verifier, conformidad-verifier, steward): frontmatter harness (name/description/tools) + columnas fila (id/schema/estado/dictamina/delega) + cuerpo = prompt canónico — el rol se LEE, no se redacta; sellados por la forja; nota de una línea en el roster del crisol. Deuda declarada: hash de agents en registry.json (parkeado).
- MIGRATION_STRATEGY: N/A (DDL solo aditivo: sin tablas nuevas — rama y agente ya declaradas en el manifiesto desde v2.0.0)
- ITER-2: FAIL de FIDELIDAD/CREDITO del scope-verifier → (1) tronco adelgazado DE VERDAD: nota de roster compactada + rama 002-migraciones-ddl extraída (segunda rama; el bloque RAMAS ya rutea 2); (2) refs recíprocas: adr:0018 agregado a esta fila; (3) regla "delega: lo resuelve el orquestador" + precedencia dictamina-manda depositadas en ADR 0018 §4; (4) endoso explícito: la forja sella TAMBIÉN ramas/ (ley que rutea al contexto viaja sellada — coherente con la cuarentena del ADR). Hallazgo del steward sin {DIFF_RANGE}: by-design (juzga planes pre-código, contrato {PLANES}). EXCEPCIÓN ONE-TIME-SCAFFOLD (con números, endosada): tronco crisol 589→591 (+2 neto) — contenido NORMATIVO −12 líneas (2 extracciones), andamiaje del mecanismo +14 por única vez (bloque RAMAS + intro); toda rama futura = +1 línea generada vs −N de contenido: la pendiente es decreciente desde acá.
- RETRO: la corrida que instaura "el tronco solo adelgaza" casi lo viola por el costo del andamiaje — un decreto con métrica necesita baseline y excepción de bootstrap declaradas EN el plan, no descubiertas por el verificador; y el roster canónico probó su valor en su primera corrida: los FAIL los cazaron los mismos prompts que esta corrida deposita (el sistema ya se audita con sus propias piezas).

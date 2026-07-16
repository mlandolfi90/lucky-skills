---
id: 2026-07-16-ramas-agentes-canonicos
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "v2.2.0 — T2: mecanismo de ramas con cuarentena + guardianes canónicos"
tier: "completo (toca proyectar.py/forja + establece los patrones rama y agente-canónico en la ley)"
target: "pc-local (Git-Bash del operador — forja la familia; directiva de sesión del operador)"
model: "fable (uniforme — Compuerta respondida por el operador en esta sesión)"
ley: "v2.1.0 (recién forjada y publicada en esta sesión)"
iteraciones: "2/3"
runState: wip
veredictos: []
refs: [adr:0018, adr:0016, adr:0017, corrida:2026-07-16-escalera-diagnostico-microfix]
---
- ORIGEN: tranche T2 del backlog aprobado (debate 2026-07-16); lección del RETRO de T1 aplicada: el ADR de patrón se deposita AL ABRIR, no tras un FAIL.
- Alcance: [T2a] ADR 0018 (el árbol vivo: ramas + cuarentena + guardianes canónicos). [T2b] mecanismo de RAMAS en proyectar.py — bloque <!-- RAMAS:BEGIN/END --> del tronco regenerado desde <skill>/ramas/*.md (patrón blockinfile); SOLO ramas canal:estable y estado LIVE/EN_DUDA entran al índice (cuarentena: canal:propuesta NO rutea hasta endoso del operador); lint extendido (ramas sin bloque en el tronco = hallazgo). [T2c] test-ramas.sh (indexado, cuarentena, idempotencia, drift). [T2d] primera rama real: crisol/ramas/001-builds-de-imagen-ci.md — extrae del tronco la regla condicional "builds de imagen: gate-test horneado en CI" (gatillo: el artefacto es una imagen) — el tronco ADELGAZA y estrena el mecanismo. [T2e] guardianes canónicos en plugins/lucky/agents/ (quality-auditor, design-verifier, leak-verifier, scope-verifier, conformidad-verifier, steward): frontmatter harness (name/description/tools) + columnas fila (id/schema/estado/dictamina/delega) + cuerpo = prompt canónico — el rol se LEE, no se redacta; sellados por la forja; nota de una línea en el roster del crisol. Deuda declarada: hash de agents en registry.json (parkeado).
- MIGRATION_STRATEGY: N/A (DDL solo aditivo: sin tablas nuevas — rama y agente ya declaradas en el manifiesto desde v2.0.0)
- ITER-2: FAIL de FIDELIDAD/CREDITO del scope-verifier → (1) tronco adelgazado DE VERDAD: nota de roster compactada + rama 002-migraciones-ddl extraída (segunda rama; el bloque RAMAS ya rutea 2); (2) refs recíprocas: adr:0018 agregado a esta fila; (3) regla "delega: lo resuelve el orquestador" + precedencia dictamina-manda depositadas en ADR 0018 §4; (4) endoso explícito: la forja sella TAMBIÉN ramas/ (ley que rutea al contexto viaja sellada — coherente con la cuarentena del ADR). Hallazgo del steward sin {DIFF_RANGE}: by-design (juzga planes pre-código, contrato {PLANES}). EXCEPCIÓN ONE-TIME-SCAFFOLD (con números, endosada): tronco crisol 589→591 (+2 neto) — contenido NORMATIVO −12 líneas (2 extracciones), andamiaje del mecanismo +14 por única vez (bloque RAMAS + intro); toda rama futura = +1 línea generada vs −N de contenido: la pendiente es decreciente desde acá.

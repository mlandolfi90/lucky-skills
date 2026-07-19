---
id: adr:0023
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-17
supersede: null
superseded_by: null
refs: [corrida:2026-07-17-equipo-saber, adr:0021, adr:0020, adr:0018, adr:0005]
---

# 0023 — El saber tiene equipo: agente destilador + skill saber

## Contexto

El sistema tiene DOS ejes de documentación con enforcement asimétrico.
**Documentar-para-usar** ganó equipo ayer (ADR 0020/0021): un autor dedicado
(`manualizador-2`), un juez que gatea (`lector-cero`) y huella mecánica
(`doc_veredicto:` validado por lint). **Documentar-para-aprender** tiene tres
piezas sueltas y ninguna cierra el lazo:

1. Un hook observador (`bitacora-observar.sh`, SessionEnd) que **cuenta**
   señales conocidas — no destila nada.
2. `/bitacora cosechar`, que sí destila — pero **solo cuando el operador la
   invoca a mano**, y solo mira el log de conteos, no los RETROs de las
   corridas.
3. crisol §4 paso 8 «Destilación»: **"opcional, NO bloqueante"**, ejecutada por
   el líder *si se acuerda*.

La evidencia de que eso falla es de hoy mismo: la corrida
`el-verde-significa-algo` cerró con un RETRO valioso y **cero fichas propuestas
en el acto del cierre**. El inventario a pedido del operador halló: 2 fichas en
`mcp-inbox` sin mergear, 3 lecciones solo en el parking, 1 solo en un RETRO
sellado, **0 en LIVE**. Documentar es guardar; aprender es que el sistema te la
devuelva solo cuando el síntoma vuelve — y solo la bitácora LIVE se consulta
por síntoma.

El tramo administrativo tampoco tiene dueño: las tools MCP existen sueltas
(`saber_mergear`, `saber_metricas`, `saber_gate_check`, `saber_telemetria`) sin
skill que las orqueste, y la promoción CANDIDATE→LIVE es "acto deliberado del
humano" (bitacora §Capturar 4) sin procedimiento que se la presente.

Mandato: /goal del operador 2026-07-17 — *"planifica y ejecuta sin mi
intervencion la creacion de un agente y una skill para
(saber/aprendizaje/conocimiento)"*. La delegación cubre la **creación**; la
gobernanza del saber (qué entra a main, qué es verdad) queda donde estaba: en
el operador (*"tu no vas a cosechar nada que yo no entienda y autorice"*,
2026-07-17).

## Decisión

1. **Agente canónico `destilador`** (`plugins/lucky/agents/destilador.md`) — el
   espejo del manualizador para el eje aprender. Lee los ARTEFACTOS de la
   corrida/sesión (fila con su RETRO, postmortems, diagnósticos, microfixes) y
   devuelve **borradores de ficha** con el shape de `saber_proponer_ficha`
   (síntoma, tipo, causa raíz, acción, anti-acción, prevención, scope,
   evidencia) o `NADA COSECHABLE: <por qué>` — jamás inventa cosecha para
   justificar el spawn.
   - **Read-only por construcción**: sin `Write`/`Edit`, sin MCP. El juicio de
     destilación es suyo; el **acto** de proponer es del flujo que lo spawnea.
     Separar juicio de acto evita darle superficie de escritura a un subagente
     y mantiene UNA garganta por donde pasa toda propuesta.
   - La doctrina de captura es la de bitacora §Capturar (síntoma observable,
     evidencia real, cero secretos) — **referenciada, no re-enunciada** (fuente
     única).
2. **Skill `saber`** (`plugins/lucky/skills/saber/`) — administra el ciclo del
   conocimiento central que nadie administraba:
   - `/saber` — estado del ciclo (inbox pendiente, CANDIDATEs, LIVE, STALE),
     read-only.
   - `/saber revisar` — la bandeja `mcp-inbox`, **ficha por ficha**: endoso del
     operador → `saber_mergear` ESA ficha; rechazo → se descarta anotando el
     porqué. Jamás batch.
   - `/saber promover <ID>` — CANDIDATE→LIVE, solo a orden explícita.
   - `/saber podar` — presenta candidatos a poda/ascenso (los criterios de
     bitacora §Mantener); decide el operador.
   - `/saber destilar <refs>` — spawnea al `destilador`, recibe borradores,
     **valida cada uno con `saber_gate_check` (dry-run: lint + leak-scan, cero
     side effects)** y propone los que pasan al inbox con `saber_proponer_ficha`
     (nunca main); parkea cada propuesta con su branch y reporta qué propuso y
     qué no (con el porqué del gate).
   - **Fail-open sin MCP**: borradores a `/idea` (parking local); la skill
     nunca bloquea ni pierde una lección por falta de connector.
3. **El gatillo deja de depender de memoria** — crisol §4 paso 8: el chequeo de
   los disparadores objetivos se REGISTRA SIEMPRE al cierre en el campo
   `BITACORA:` de la fila (refs de lo propuesto o `N/A (sin disparador)`);
   disparador con sí → spawn del `destilador`. **Sin gate nuevo, sin ID de
   matriz nuevo**: el jidoka queda intacto (el gate no bloquea por la
   Bitácora); la dureza es la huella — un cierre sin el campo se ve en la fila.
4. **Gobernanza sin cambios**: proponer al inbox (rama `mcp-inbox/*`, jamás
   main) es el único acto sin endoso; mergear, promover y podar exigen endoso
   del operador **por ficha** ("un sí no es un sí al lote").

## Consecuencias

- La asimetría se cierra: ambos ejes de documentación tienen autor dedicado +
  procedimiento con huella. El pipeline completo queda:
  incidente → destilador (borrador) → inbox (propuesta) → operador
  (merge = CANDIDATE) → operador (promueve = LIVE) → consulta por síntoma.
- **Costo declarado**: +1 spawn (`destilador`) por cierre de corrida CON
  disparador; cero spawns sin disparador; el registro `BITACORA: N/A` cuesta
  una línea.
- **Límite explícito**: el `destilador` destila artefactos de corrida; el log
  del observador sigue siendo territorio de `/bitacora cosechar`
  (FRECUENCIA/INTENSIDAD). Complementarios, sin superposición — dos insumos,
  dos puertas, la misma bandeja.
- **Límite de la superficie MCP (arqueología 2026-07-17)**: NINGUNA tool MCP
  enumera las ramas `mcp-inbox/*` pendientes — el `branch` que devuelve
  `saber_proponer_ficha` es el ÚNICO handle para mergearla. Por eso la skill
  `saber` persiste cada propuesta como **línea de parking en `docs/IDEAS.md`**
  (la bandeja local que lee `/saber revisar`): una propuesta cuyo branch no se
  parkeó es invisible vía MCP y se declara como tal, no se inventa. Además,
  `saber_gate_check` da la validación **dry-run** (lint + leak-scan sin
  commitear) previa a `saber_proponer_ficha`. Y ni la promoción CANDIDATE→LIVE
  ni la poda tienen tool que las ejecute **por diseño** (`saber_mergear` nunca
  promueve a LIVE; el MCP nunca escribe `usos`/`estado`/`scope`) → `/saber
  promover` y `/saber podar` son **subcomandos GUIADOS v1**: la skill presenta y
  registra el endoso; el acto lo ejecuta el operador en `lucky-saber`.
- **Deuda declarada**: (a) poda/ascenso quedan como procedimiento guiado v1 (la
  skill los presenta; no hay automatización); (b) telemetría del destilador
  (borradores endosados vs descartados — insumo de recalibración, como en ADR
  0021) queda para cuando `saber_telemetria`/`saber_metricas` acumulen datos.
- **Considerado y descartado a propósito**:
  - Que el `destilador` llame MCP él mismo — separaría el acto de la garganta
    única y daría superficie de escritura a un subagente.
  - Cosecha con **merge automático** — violaría la propiedad humana sobre la
    promoción (bitacora §Capturar 4, anti documentation-theater) y la directiva
    dura del operador.
  - Un ID de matriz `DESTILACION` — convertir el aviso en gate pelearía con el
    jidoka (crisol §4 paso 8, textual). Si ~3 RETROs futuros muestran cierres
    con `BITACORA:` mentiroso, esa evidencia abre SU corrida (disparador
    kaizen, crisol §6).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.8.0` (cache local, NO la ley).**

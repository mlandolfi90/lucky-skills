---
id: PLAN-saber-fase2-promocion-inmediata
schema: plan/1
tipo: plan
estado: VIGENTE
creado: 2026-07-24
refs: [corrida:2026-07-24-saber-fase2-promocion-inmediata, adr:0023, adr:0027, adr:0015, adr:0018]
nota: "FASE PIN INCOMPLETA a propósito: el contrato cross-lane (server del saber, lane Hackaton) NO está pineado todavía — su corrida ni está abierta. La INGENIERÍA queda EN ESPERA de ese pin. Este plan captura el diseño y la frontera para no hacer trabajo dependiente antes de que la dependencia decida (lección forjar-tras-contrato-de-sesion-dependiente)."
---
# Plan — corrida `2026-07-24-saber-fase2-promocion-inmediata`

GO directo del operador. **Norte que hace el cambio coherente con su ley:** el principio "el
humano decide qué es verdad" NO muere — se MUEVE de gate-pre-LIVE a curaduría-posterior
(la destilación). Cambia el MOMENTO del juicio, no su existencia.

## El cambio de modelo

HOY: captura → CANDIDATE → (endoso humano ficha-por-ficha) → LIVE · "contar ≠ ungir" · "sin
evidencia real NO entra". FASE 2: captura → LIVE directo · la cita causal pasa a ser HISTORIAL
de cómo/cuándo funcionó (no gate) · el juicio humano = ritual `/saber destilar` (curaduría batch:
consolidar + fusionar cuasi-duplicados + forjar el canónico + PROPONER poda de evidencia-cero a
~30d, reversible=archivar; el humano confirma) · `endosar.py` como override manual.

## Mapa DEROGAR / MODIFICAR / CONSERVAR (arqueología, con archivo:línea)

**DEROGAR (el gate pre-LIVE muere)** — vía ADR NUEVO con `superseded_by` (los registros son
inmutables, no se editan):
- `saber/SKILL.md:227` "Endoso POR FICHA… jamás batch" (núcleo del gate) · `:96` "PROHIBIDO
  BATCH" · `/saber promover` (`:103,111,114`) pierde su objeto · el contrato "saber_mergear
  nunca promueve a LIVE" + estado CANDIDATE (`:88,108,230`) — **doctrina lucky; el tool lo pinea Hackaton**.
- Puntos de gate en ADR 0023:73,90 · 0027:49 · 0015:35 → derogados por el ADR Fase 2.

**MODIFICAR (cambian de forma, no desaparecen):** description+disparadores (`:6,8,21`: cae
"promové", gana "curá/destilá") · "contar ≠ ungir" (`:150,203`) → cita = HISTORIAL · `/saber
revisar` (`:66,85`) → override excepcional · crisol `:530,513` → la Destilación es el acto de
curaduría · bitacora `:95,215,180,185` → poda de salida reversible · el escenario
`cumplimiento/escenarios/endoso.md` + `GUIA-SKILLS.md:96` (con diente de `test-racionalizaciones.sh`)
→ reencuadrar el huésped "saber revisar" (el portón NO se borra: sigue vivo en migrar/feature).

**CONSERVAR (intacto):** `saber/SKILL.md:168` "el humano decide qué es verdad" (ancla nuclear) ·
`/saber citar` mecánica (contrato entry_id→server→content_key PINEADO en v2.10.2 — solo cambia el
ROL a historial) · `destilador.md` sigue CAPTURADOR read-only.

**DRIFT vivo a corregir (independiente de Fase 2, gratis en la pasada):** `crisol/SKILL.md:518` +
`templates/run-ledger.md:25,72` dicen que CITAS_SABER lleva `dedup_key`; el pin v2.10.2 ya lo
corrigió a `entry_id` en `/saber citar` y ADR 0027. Reescribir a `entry_id`. (Puede hacerse ya como
micro-fix separado, o al cerrar esta corrida — decisión del operador.)

## El ritual `/saber destilar` Fase 2 (resolución de la colisión de nombre)

Hoy `destilar` = CAPTURAR. Fase 2 lo quiere = CURAR. Son dos fases del ciclo; no comparten verbo.
- **La captura-al-cierre NO desaparece** (crisol §4 paso 8 sigue spawneando al destilador); su
  único cambio es aguas abajo (los borradores van a LIVE directo, no a mcp-inbox). Gatillo propio.
- **La curaduría es el ritual nuevo, humano, batch:** (1) consolidar LIVE + sus historiales de
  cita; (2) fusionar cuasi-duplicados semánticos → forjar el canónico (trabajo humano/otro agente,
  NO el destilador); (3) PROPONER poda de evidencia-cero a ~30d, reversible (el humano confirma) →
  INVOCA `/saber podar` (única garganta de poda, extendida), jamás reimplementa.
- **Insumo de RAG:** el núcleo de valor es la fusión de cuasi-dups (los exactos ya los dedup el
  content_key en captura); cadencia barata (sugerida al cierre de corrida o por umbral acumulado).
- **Regla de fusión (RAG, verificada con 12 escépticos opus: 0/12 cuasi-dups aparentes debían
  fusionarse — lo "parecido" es complementario, vinculado por `refs`). A HORNEAR en el ritual:**
  (a) discriminante de duplicación = **CAUSA-RAÍZ + ACCIÓN**, jamás síntoma/vocabulario (lo que
  "suena" parecido no lo es); (b) **default ante duda = NO fusionar** (la fusión es irreversible y
  destruye conocimiento); (c) el comando **PROPONE, nunca fusiona solo** — el humano confirma cada
  fusión; (d) la UX muestra **causa+acción de cada par candidato** para que el humano juzgue por lo
  que importa, no por cómo suena. (Lección = ficha `CAND-d471300b18b2`.)

## FASE PIN — lo que DEBE pinear Hackaton ANTES de que yo forje (ingeniería EN ESPERA)

La ingeniería (rewrite de la skill + ADR final) NO arranca hasta que Hackaton cierre su corrida
server y pinee estos 7 contratos (su lane; yo no los puedo definir):
1. Cómo entra LIVE directo (¿saber_proponer_ficha/capturar_idea escriben LIVE? ¿saber_mergear pasa
   a promover? ¿tool nueva?).
2. ¿Sobrevive el estado CANDIDATE y las ramas `mcp-inbox/*`? (define si `/saber revisar` y `/saber
   promover` mueren o se re-significan — gobierna cuánta prosa cambia).
3. **Contrato de la poda reversible (el más pesado):** qué tool escribe `estado=archivado`, cuál
   restaura, quién computa los candidatos evidencia-cero sobre la ventana ~30d. Hoy el MCP no
   escribe estado → sin esto, Fase 2 no cierra.
4. ¿El server exige evidencia real en la captura directa? (para no perder la capa que hoy daba el
   endoso pre-LIVE — RIESGO real: Fase 2 saca una de las dos capas de evidencia).
5. Contrato de `endosar.py` como override.
6. ¿Sigue `saber_gate_check` (dry-run lint+leak) como validación previa a un LIVE directo?
7. Coalesce content_key: MOOT para fichas nacidas-LIVE; confirmar que se mantiene para CANDIDATE
   legacy en vuelo y qué pasa con ellas al flipear.
Además: los shapes de los tools nuevos del ritual (`saber_destilar_proponer`, `saber_historial`,
campos nuevos de `saber_telemetria`) — mantener la doctrina FLEXIBLE hasta el pin.

## Supuestos del plan (ADR 0025 — tope 5). OJO: 1-3 son DECISIONES PENDIENTES de Hackaton, no asunciones firmes.

1. **CANDIDATE + `mcp-inbox/*` se eliminan** del flujo saber (captura→LIVE directo); `/saber
   promover`+`/saber revisar` sobreviven solo como override. — **Pendiente de confirmación de Hackaton (FASE PIN #2).**
2. **El server gana escritura de estado (`archivado`) + restaurar**, habilitando la poda
   reversible; `/saber podar` deja de ser guiado-a-mano. — **Pendiente (FASE PIN #3).** Sin esto Fase 2 no cierra.
3. **La captura directa exige evidencia en el server** (o todo pasa por el destilador), para no
   perder la capa de evidencia pre-LIVE. — **Pendiente (FASE PIN #4).**
4. **`/saber destilar` se reserva a la CURADURÍA;** la captura-al-cierre se reubica bajo otro
   gatillo. — Decisión de lucky-skills (mía), firme.
5. **`/saber citar` (ADR 0027) queda congelada**, solo cambia su semántica a historial; el coalesce
   del rename se mantiene solo para CANDIDATE legacy. — Firme (mío), depende de #1 para el legacy.

**Estado del plan:** DISEÑO COMPLETO, INGENIERÍA EN ESPERA del pin de Hackaton. Cuando su corrida
server cierre, resuelvo los supuestos 1-3 con sus contratos reales, escribo el ADR Fase 2 + el
rewrite de la skill con los shapes pineados, verifico (roster), cierro, y forjo UN release. No antes.

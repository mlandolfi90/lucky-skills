---
id: 2026-07-18-saber-mcp-actualizado-vs-equipo-saber
schema: diagnostico/1
tipo: diagnostico
estado: RESPONDIDO
creado: 2026-07-18
sintoma: "¿El agente destilador y la skill saber (v2.7.0) siguen funcionando adecuadamente contra la última actualización del MCP saber?"
reproduccion: "saber_frescura → saber_head=119c0865321e (ayer 2f1a410eeb90) · ToolSearch saber_* → 12 tools, shapes idénticos · saber_index(candidate) → aparece CAND-873c5acb10f3 nueva"
zona_sospechada:
  - "plugins/lucky/skills/saber/SKILL.md · sección «/saber revisar» (el merge)"
  - "plugins/lucky/agents/destilador.md:74-77 (regla 5 «posible dup»)"
  - "docs/decisions/0023-el-saber-tiene-equipo.md · «Límite de la superficie MCP»"
hipotesis:
  - {h: "La superficie de tools que la skill/agente CONSUMEN no cambió → funcionan igual", evidencia: "12 tools saber_* con nombres y shapes byte-idénticos a la arqueología de ayer; saber_proponer_ficha y saber_gate_check con los mismos required/params; saber_mergear con el mismo contrato (anexa CANDIDATE, nunca promueve a LIVE)", verificar: "ya verificado: schemas leídos hoy vía ToolSearch (read-only)"}
  - {h: "El «límite MCP: ninguna tool enumera el inbox mcp-inbox/*» SIGUE VIGENTE", evidencia: "ninguna tool nueva de enumeración (no existe saber_inbox / saber_pendientes / saber_listar_ramas); mis 3 propuestas de ayer no aparecen en saber_index (siguen en sus ramas sin mergear), exactamente como el ADR 0023 predice", verificar: "ya verificado: saber_index(incluir_candidate) no las muestra"}
  - {h: "La actualización del server tocó el GATE DE ENDOSO (dedup por similitud), NO la superficie de tools", evidencia: "sha del server cambió + ficha CANDIDATE nueva CAND-873c5acb10f3 en main, cuyo tema es literalmente «poné el chequeo de similitud en el GATE DE ENDOSO, no en la escritura ciega»", verificar: "NO confirmable read-only: saber_mergear MUTA (es peldaño 1+, no diagnóstico); su descripción sigue diciendo «gate server-side» genérico, igual que ayer — no declara el chequeo de similitud explícitamente"}
bitacora_match: CAND-873c5acb10f3
escalon_recomendado: microfix
tope_sugerido: microfix
target_observado: "MCP saber servido vía lucky-mcp (saber_head=119c0865321e, fresh) — observación read-only; repo lucky-skills en pc-local"
refs: [adr:0023, corrida:2026-07-17-equipo-saber]
---
## Veredicto: el destilador y la skill saber FUNCIONAN adecuadamente. Nada roto.

El MCP saber SÍ se actualizó desde ayer (`saber_head` 2f1a410eeb90 → 119c0865321e,
`fresh`). Pero la actualización **no tocó la superficie que el equipo del saber
consume**:

- **Tools idénticas.** Las 12 `saber_*` (buscar, capturar_idea, frescura, mergear,
  ficha, gate_check, index, metricas, proponer_ficha, refs, senal, telemetria)
  siguen presentes con nombres y shapes byte-idénticos. El destilador propone con el
  shape correcto de `saber_proponer_ficha`; la skill valida con `saber_gate_check`
  igual que ayer.
- **El «límite MCP» sigue vigente.** No nació ninguna tool que enumere las ramas
  `mcp-inbox/*` pendientes. Por eso la bandeja local en `docs/IDEAS.md` sigue siendo
  el mecanismo correcto — la asunción central del ADR 0023 y de `/saber revisar` no
  se rompió. Prueba viva: mis 3 propuestas de ayer NO aparecen en `saber_index`
  (siguen en sus ramas sin mergear), exactamente como el diseño predice.

## Lo nuevo (hilo abierto, NO bloqueante)

Apareció una ficha CANDIDATE nueva en main, **CAND-873c5acb10f3**, sobre *"detectar
casi-duplicados en un catálogo que se deduplica por fingerprint LITERAL → poné el
chequeo de similitud en el GATE DE ENDOSO"*. Sumado al sha nuevo, sugiere que la
actualización trabajó en **dedup por similitud en el gate de endoso** (el merge),
no en las tools.

Si eso llegó a `saber_mergear`, el efecto sobre el equipo del saber es **aditivo, no
rompe nada**:
- El `destilador` YA está alineado: su regla 5 dice *"PROPONELO igual marcando
  «posible dup de <ID>»"* — complementa un dedup por similitud, no choca con él.
- `/saber revisar` podría querer MENCIONAR que el merge ahora puede avisar de fichas
  similares (para que el operador lo espere). Es drift de DOCUMENTACIÓN, no de
  comportamiento.

**No es confirmable desde el peldaño 0:** `saber_mergear` muta, así que no puedo
verificar read-only si el chequeo de similitud ya está activo. La descripción de la
tool no lo declara explícitamente (sigue diciendo "gate server-side" genérico). Para
cerrar el hilo haría falta un merge real (acto del operador) que exhiba —o no— el
aviso de similares; recién con esa observación un microfix documentaría la línea en
`/saber revisar`. Hasta entonces: N/D sobre si el chequeo está activo.

## Nota de proceso (ley viva)

La skill `diagnostico` se cargó de la caché del harness en **v2.4.0**
(`…/plugins/cache/lucky-skills/lucky/2.4.0/…`), mientras el repo está en **v2.7.0**.
Por la ley viva seguí el procedimiento del repo (estable entre esas versiones). Es
una instancia en vivo de **CAND-c0cb1839f36e** (caché de plugins vieja: el `Base
directory` apunta a un tag menor al publicado). LEY: v2.7.0 (repo).

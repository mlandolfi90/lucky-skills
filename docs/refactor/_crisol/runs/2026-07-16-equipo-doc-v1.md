---
id: 2026-07-16-equipo-doc-v1
schema: corrida/1
tipo: corrida
estado: ACTIVE
creado: 2026-07-16
branch: main
titulo: "Equipo de documentación v1 — lector-cero gatea el pase a VIVA"
tier: "completo (>1 archivo de código; establece patrón: primer verificador de registro, no de corrida)"
target: "pc-local (la forja: skills/agentes/scripts corren en esta PC — directiva explícita del operador)"
model: "fable (uniforme)"
ley: "v2.4.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "3/3 (convergió: APPROVE ×3)"
runState: wip
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (la forja; directiva explícita del operador)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: A 2 filas nuevas + 2 líneas de transición · B rama nueva, 5 ediciones con caso nombrado · C AGREGA sin caso legal (PIN 4)"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: ~70/~110/2 · tronco 100 + rama 70 · lint 227→330, brujula 72→122; todos vs T=400"}
  - {regla: COSTURA, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: usa costuras existentes (0018 §1 ramas, §4 supersede); sin seam especulativo — 2ª corrida gana la costura al 2º cliente"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: (a) bug real SKILL.md:12 sin Agent vs :66 ordena spawn; (c) pagado con ADR 0021; (b) re-etiquetado a AGREGA en C"}
  - {regla: CREDITO, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: ADR 0021 depositado al abrir y citado por § en los 3 carriles; ninguno construye verificador-frescura (§8)"}
refs: [concejo:2026-07-16-equipo-doc, adr:0018, adr:0019, adr:0020, adr:0021, plan:PLAN-equipo-doc-contratos]
---
- ORIGEN: el operador preguntó por qué el manualizador es UN agente y no un
  equipito. Debate de diseño → concejo de 5 jueces frescos
  (`concejo:2026-07-16-equipo-doc`, 5/5 APRUEBA_CON_CAMBIOS, enmiendas E1–E8) →
  endoso del operador ("vamos con 1" = alcance v1: un solo agente nuevo,
  verificador-frescura diferido). El endoso se convoca como ADR 0021 (rama
  `crisol/ramas/003-decisiones-convocables` — gatillo: juicio de diseño del
  operador que hoy moriría en el chat).
- Alcance: (1) ADR 0021 — el gate de doc exige que el manual SIRVA, no solo que
  exista; (2) agente canónico `lector-cero` (juzga por LECTURA, sin Bash,
  dictamina `DOC_SIRVE`); (3) supersede del `manualizador` (ADR 0018 §4: gatillo
  de corrección + `{TROPIEZOS}`, dueño del sidecar de cobertura, modo dictamen,
  deja de escribir `doc:`); (4) skill `feature` — regla dura 2 ampliada,
  columnas `doc_veredicto`/`audiencia`, bucle de 2 rondas fail-closed, `Agent`
  en allowed-tools; (5) sidecar `docs/manual/_cobertura.yaml` + señal de
  frescura por cursor SHA dentro de `brujula.sh`; (6) chequeos nuevos en
  `registros-lint.py`; (7) `leak-scan.sh` en el gate de doc.
  FUERA DE ALCANCE (deuda declarada por el concejo, E5/YAGNI): el agente
  `verificador-frescura` — su dictamen lo cubre el manualizador en modo
  dictamen hasta que la telemetría justifique el agente propio.
- WORKTREE: 1 untracked al abrir — `plugins/lucky/.orphaned_at` (marcador del
  harness de plugins: un epoch en ms, no es trabajo del repo ni basura de
  crash). Decisión: se deja INTACTO y se declara; no entra en ningún commit.
- ITER 1 — Steward: REJECT ×3. Los sets de archivos eran DISJUNTOS (cero
  colisión física); la colisión fue 100% CONTRACTUAL y formaba un CICLO (A
  necesita el formato de C · B el nombre de A · C la forma de B). Ningún orden
  de carriles resuelve un ciclo → FASE PIN: los 3 contratos se fijan en UN
  artefacto (`plan:PLAN-equipo-doc-contratos`) y cada carril los cita. Sin
  código escrito en esta iteración (el REJECT cayó sobre los planes, que es el
  punto donde debe caer: shift-left).
- ITER 2 — Steward: A APPROVE · B REJECT · C REJECT (defectos PROPIOS, ya no
  contractuales: el PIN disolvió el ciclo). B: la rama nueva nacía SIN sello
  ancla → `forjar-release.sh` habría abortado la forja; y su prosa describía
  FALSO el contrato de `leak-scan.sh` (:26 vs :27-31) — ley sellada que miente
  sobre el código invita a que un mantenedor futuro desarme el `git add` y el
  falso-verde vuelva. C: el gate de doc quedaba INALCANZABLE — el `return` del
  caso lazy corría ANTES del chequeo (iv), y como `docs/manual/` hoy no existe,
  una feature VIVA sin `doc_veredicto.estado: PASA` pasaba el lint EN VERDE.
  Causa raíz de ATOMICIDAD (dos responsabilidades en una función): la laziness
  del sidecar apagaba el gate. [DRIFT-001] materializado dos veces — el mismo
  falso-verde que el PIN 1 mató en la FORMA del campo, reaparecido en la
  ALCANZABILIDAD del chequeo.
- ITER 3 — Steward: APPROVE ×3. Convergió. B saldó el sello ancla (footer
  byte-idéntico a crisol/ramas/003, medido n=1 con el regex real del script) y
  reemplazó la cláusula falsa por lo que `leak-scan.sh:27-31` HACE. C partió
  `_lint_cobertura` / `_lint_gate_doc` con call-sites independientes: ningún
  `return` del sidecar puede volver a apagar el gate, y el skip único es por
  ausencia de SUJETO (`docs/features/` lazy), no de chequeo. Sets disjuntos →
  A · B · C escriben en paralelo.
- MIGRATION_STRATEGY: N/A (sin DDL)
- RETRO: <pendiente al cierre>

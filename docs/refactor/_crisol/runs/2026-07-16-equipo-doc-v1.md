---
id: 2026-07-16-equipo-doc-v1
schema: corrida/1
tipo: corrida
estado: ESCALATED
creado: 2026-07-16
branch: main
titulo: "Equipo de documentación v1 — lector-cero gatea el pase a VIVA"
tier: "completo (>1 archivo de código; establece patrón: primer verificador de registro, no de corrida)"
target: "pc-local (la forja: skills/agentes/scripts corren en esta PC — directiva explícita del operador)"
model: "fable (uniforme)"
ley: "v2.4.0 (verificada — git ls-remote: máximo remoto == sello local)"
iteraciones: "3/3 (convergió: APPROVE ×3)"
runState: closing
cierre: "2026-07-16 · ESCALATED por techo (3/3) · el trabajo vive en los WIP-commits e60f7de·555391e·d761033·96d5ab8 · sucede: corrida:2026-07-16-equipo-doc-v1-fix"
veredictos:
  - {regla: TARGET, veredicto: PASS, quien: líder, evidencia: "pc-local (la forja; directiva explícita del operador)"}
  - {regla: MODEL, veredicto: PASS, quien: líder, evidencia: "fable (uniforme)"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: A 2 filas nuevas + 2 líneas de transición · B rama nueva, 5 ediciones con caso nombrado · C AGREGA sin caso legal (PIN 4)"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: ~70/~110/2 · tronco 100 + rama 70 · lint 227→330, brujula 72→122; todos vs T=400"}
  - {regla: COSTURA, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: usa costuras existentes (0018 §1 ramas, §4 supersede); sin seam especulativo — 2ª corrida gana la costura al 2º cliente"}
  - {regla: CASOS_LEGALES, veredicto: PASS, quien: steward, evidencia: "shift-left iter3: (a) bug real SKILL.md:12 sin Agent vs :66 ordena spawn; (c) pagado con ADR 0021; (b) re-etiquetado a AGREGA en C"}
  - {regla: CREDITO, veredicto: PASS, quien: scope-verifier, evidencia: "ADR 0021 ACEPTADA en b1ddcac, decision/1 válido, refs recíprocas ambas direcciones; 8/8 puntos materializados; tabla decision no es sellado:true → sin entrada en sellos.json (correcto)"}
  - {regla: REGLA0, veredicto: PASS, quien: quality-auditor, evidencia: "pc-local: lint exit 0 + proyectar --check drift 0 + 13/13 suites + 9 pruebas NEGATIVAS que mordieron + 1 control positivo verde"}
  - {regla: TEST_COVERAGE, veredicto: PASS, quien: quality-auditor, evidencia: "bitacora(4) cargar(1) crisol(6) ley(1) management(1) = 13/13; gate de doc y sidecar sin suite automatizada → cubiertos por prueba negativa manual (brecha declarada)"}
  - {regla: ZERO_LEAK, veredicto: PASS, quien: leak-verifier, evidencia: "leak-scan --staged exit 0 + árbol completo exit 0 + 20 artefactos a mano + barrido independiente de 182 archivos"}
  - {regla: INDEPENDENCIA, veredicto: PASS, quien: líder, evidencia: "4 verificadores FRESCOS (quality/leak/design/scope), input = solo el diff staged; el líder no verificó su propio trabajo — de hecho el ingeniero B le cazó al líder el ADR sin sello"}
  - {regla: SCOPE_CREEP, veredicto: PASS, quien: scope-verifier, evidencia: "10/10 archivos mapean 1:1 a los 7 ítems; cero huérfanos/faltantes; grep verificador-frescura = 0 hits en agents/skills/scripts (FUERA DE ALCANCE respetado: el 'vamos con 1' se honró)"}
  - {regla: PARKING, veredicto: PASS, quien: scope-verifier, evidencia: "verificador-frescura → ADR 0021 §8 + Consecuencias; paridad prosa↔script de las otras 2 señales → Consecuencias:138-141. Ambas con captura viva"}
  - {regla: OPEN_CLOSED, veredicto: PASS, quien: design-verifier, evidencia: "3 archivos nuevos + 2 funciones + 2 call-sites + bloque nuevo; ediciones a estable con caso legal declarado (manualizador.md:15,19 transición · feature:12 bug (a) · feature regla 2 contrato (c))"}
  - {regla: ATOMICIDAD, veredicto: PASS, quien: design-verifier, evidencia: "una responsabilidad por unidad; CITACIÓN por tamaño: registros-lint.py quedó en 423 > T=400 → resuelto por NOMBRE (larga-legítima, no responsabilidad múltiple); el shift-left había proyectado 330"}
  - {regla: COSTURA, veredicto: PASS, quien: design-verifier, evidencia: "el contrato del sidecar tiene DOS consumidores REALES ya implementados (awk brujula.sh + PyYAML lint), no uno hipotético; PIN 4 difiere la costura al 2º cliente"}
  - {regla: LISKOV, veredicto: PASS, quien: design-verifier, evidencia: "lector-cero y manualizador-2 llenan agente/1 con el mismo shape que sus 6 hermanos; el líder los spawnea por nombre sin enterarse"}
  - {regla: INTERFACE_SEGREGATION, veredicto: PASS, quien: design-verifier, evidencia: "lector-cero SIN Bash/Write/Edit (juzga) vs manualizador-2 CON (escribe piezas+sidecar, necesita git rev-parse); cada contrato expone solo lo que su cliente usa"}
  - {regla: PIN_TOTAL, veredicto: "N/A", quien: design-verifier, evidencia: "el diff no toca manifiestos de deps; subprocess es stdlib y git es toolchain de ambiente, no paquete pineable"}
  - {regla: MIGRATION, veredicto: "N/A", quien: gate, evidencia: "sin DDL"}
  - {regla: CONFORMIDAD, veredicto: "N/A", quien: líder, evidencia: "tooling sin capas (precedente: mismas corridas previas de la forja)"}
  - {regla: TARGET_ENV, veredicto: "N/A", quien: líder, evidencia: "pc-local sin @env"}
  - {regla: RESPONSIVE, veredicto: "N/A", quien: líder, evidencia: "sin UI"}
  - {regla: FUENTE_VERDAD, veredicto: "N/A", quien: líder, evidencia: "no toca testing/prod"}
  - {regla: TECHO_ITER, veredicto: FAIL, quien: líder, evidencia: "3/3 consumidas (REJECT·REJECT·APPROVE) y la verificación de la iter 3 cerró en FAIL de scope → el ciclo siguiente sería el 4º. Techo alcanzado: se DETIENE, decide el operador"}
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
- VERIFICACIÓN (iter 3) — roster fresco: quality PASS · leak PASS · design PASS ·
  **scope FAIL**. El quality-auditor NO se conformó con el verde: declaró que el
  verde base era VACUO (`docs/features/` y `docs/manual/` no existen → ambas
  funciones nuevas pegan su early-return por ausencia de sujeto), y ejerció 9
  pruebas NEGATIVAS + 1 control positivo. El gate DISCRIMINA: rojo con `VIVA`
  sin doc, rojo con `doc_veredicto: PASA` PLANO (el falso-verde estructural que
  el PIN 1 predijo), rojo con `PENDIENTE`, VERDE con la fila correcta. También
  cazó un falso-verde PROPIO (su clone traía el lint viejo porque el diff está
  staged, no commiteado) y lo corrigió antes de reportar.
- DIVERGENCIA EXACTA (techo alcanzado — decide el operador):
  `plugins/lucky/skills/feature/ramas/001-gate-de-doc.md:24` cita
  `manualizador.md:41` como la línea donde el prompt SUPERSEDED escribe `doc:`.
  Contra HEAD era CORRECTA; contra el árbol staged es FALSA: el carril A insertó
  `superseded_by:` (+1 línea) y corrió la cita a `:42`. Verificado por el líder:
  `:41` hoy dice "cross-references; jamás re-estructures…" y `:42` es la regla 5.
  Es el costo exacto del paralelismo con sets disjuntos donde B cita por NÚMERO
  DE LÍNEA un archivo que A está editando — la colisión que el COLLISION-MAP no
  ve porque no es de archivo, es de referencia.
  Por qué es FAIL y no benevolencia (el scope-verifier lo argumentó y el líder lo
  ratifica): la iter 2 rechazó a ESTE MISMO carril por ESTE MISMO defecto (prosa
  que describe falso el contrato de `leak-scan.sh`). La rama es `canal: estable`
  y LIVE — ley que RUTEA — y esa cita es la única evidencia que sostiene la regla
  load-bearing del PIN 3 ("el nombre del llamador es el único de-ruteo"). Un
  mantenedor que la verifique abre `:41`, ve otra cosa, y desarma la regla.
  FIX conocido y de UNA línea: `001-gate-de-doc.md:24` → `manualizador.md:42`.
  (Arrastre menor, artefacto de taller ya commiteado y fuera de este diff:
  `PLAN-equipo-doc-contratos.md:90` repite la cita `:41`.)
- HALLAZGOS NO BLOQUEANTES cosechados por el roster (para el operador; sin hogar
  todavía — el líder NO los captura por su cuenta estando en techo):
  1. **Defecto REAL en `scripts/leak-scan.sh:61`** (regla RUTA-ABSOLUTA): la rama
     Windows del regex está MUERTA por doble-escape (`C:\\\\Users\\\\` en ERE
     exige DOS backslashes literales) → un path Windows real NO matchea. Probado
     end-to-end con el script real: `C:\Users\alguien\x.md` → exit 0 (pasa en
     verde); `/home/otro/y.md` → exit 1. Hoy solo se atrapa de rebote por la
     regla 2 (nombre del operador hardcodeado); un path de OTRO usuario se
     filtraría en silencio. Fix: `\\` en vez de `\\\\`. El PASS de ZERO_LEAK de
     esta corrida NO depende de ese regex: el leak-verifier lo suplió con un
     barrido independiente en Python sobre 182 archivos.
  2. `registros-lint.py` quedó en 423 líneas > T=400 → los guardianes emitirán el
     nudge no-bloqueante en cada edit futuro. `main()` (169L) aún lleva los
     chequeos 1-5 inline mientras el 6 y 7 ya están compuestos.
  3. Asimetría de matcher: el lint descubre piezas con `rglob` (ve untracked), la
     brújula con `git ls-files` (solo trackeado). Dirección fail-closed (el lint
     muerde más), por eso no es FAIL.
  4. `registros-lint.py:25` declara "Dependencia: PyYAML" y ya shell-outea a git.
- MIGRATION_STRATEGY: N/A (sin DDL)
- ESCALACIÓN: techo 3/3 con FAIL de scope. Presentada al operador con los 3
  caminos; eligió (1) — cerrar ESCALATED y saldar por corrida fix-forward. El
  fix NO se aplicó acá: aplicarlo hubiera sido el workaround exacto que el techo
  prohíbe. Sucesora: `corrida:2026-07-16-equipo-doc-v1-fix` (fast-path).
  Ningún trabajo se pierde: los 10 archivos viven en los WIP-commits.
- RETRO (blameless): el techo se gastó ANTES de escribir una línea de código —
  2 de 3 iteraciones se fueron en el ciclo de contratos entre carriles paralelos,
  que el COLLISION-MAP no ve porque no es colisión de ARCHIVOS sino de
  REFERENCIAS. El proceso funcionó (los 3 REJECT eran correctos y cazaron
  falsos-verdes reales antes de producción), pero el presupuesto de iteraciones
  se consumió en coordinación, no en el problema. Dos aprendizajes con nombre:
  (a) la FASE PIN debería ser el paso 0 de todo tier completo con >1 carril —
  fijar los contratos cross-carril ANTES de mandar a planificar, en vez de
  descubrir el ciclo con el primer REJECT; (b) citar código por NÚMERO DE LÍNEA
  entre carriles paralelos es intrínsecamente frágil: el vecino inserta una línea
  y tu ley queda mintiendo. Citar por ancla de texto (la regla, el nombre) o
  aceptar el riesgo explícitamente. Ambos son candidatos a entrada de bitácora y
  a corrida futura sobre la propia skill (§6, disparador kaizen).

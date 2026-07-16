# IDEAS — parking lot (formato: YYYY-MM-DD · idea · contexto-sin-secretos)

- 2026-07-06 · [DECIDIDO — MLL] diseño anti-slop = ADOPTAR `pbakaus/impeccable` (tercero, Apache-2.0) en cada
  repo de PRODUCTO, jamás copiado a lucky-skills. Receta PIN_TOTAL: submodule `.impeccable` PINEADO a
  commit/tag exacto + `npx impeccable link --source=.impeccable --providers=claude` (el `npx impeccable
  install` pelado es floating → prohibido). Los tokens de lucky-estilo alimentan `.impeccable/design.json`
  + DESIGN.md (marca=valores, impeccable=enforcement). La skill propia `diseno` fue RETIRADA el mismo día
  (nunca llegó al registry). Candidatos futuros: (a) que `adoptar-crisol.sh` ofrezca instalar impeccable
  pineado; (b) mirror propio si el takedown-risk lo amerita (copia-de-lo-crítico §2)
- 2026-07-06 · [corrida ATOMICIDAD] Hueco A a medias: el aviso per-edit (Cambio 3) NUDGEA fuera de corrida
  pero NO fuerza el cierre — su otra raíz (una corrida que abre ACTIVE y WIP-commitea con runState: wip
  para siempre sin correr el design-verifier) sigue abierta. Ya parqueada como "endurecer la detección de
  cierre más allá de runState" (2026-06-21). Candidata a unificar ambas · hallado en el plan/corrida atomicidad
- 2026-06-11 · explorar recurso "GRAFO" de Nexum AI (@agustinbadt) — grafos de
  conocimiento para memoria/organización de agentes · fuente:
  youtube.com/shorts/UhGWH_9bqaU · capturada a mano por MLL (demo del
  futuro /idea v1.1.0)
- 2026-06-11 · mini-skill /idea: captura universal a docs/IDEAS.md, una línea,
  autoactivación ON ("anotá esto", "se me ocurrió") · diseñada en la corrida 0,
  candidata · ✅ CONSTRUIDA como v1.4.0 (2026-06-11)
- 2026-06-11 · tiers de modelo EXPLÍCITOS y AGNÓSTICOS para subagentes: antes
  de lanzar agentes, declarar (o preguntar al humano) qué tier usa cada uno
  según COMPLEJIDAD de la tarea — sencilla→tier-económico, compleja→tier-alto,
  súper-compleja→tier-frontera. Lección: el tier barato en tareas complejas
  sale CARO (rework, "nos hace trabajar más"). Agnóstico: los tiers se mapean
  a modelos concretos en UN solo lugar (hoy: sonnet/opus/fable), así sobrevive
  a modelos nuevos · candidata a enmienda de §3 del crisol (próxima release) ·
  idea de MLL
- 2026-06-15 · verificar que las skills lucky funcionen en Claude WEB (no solo
  CLI local) — prioridad principal · Ley viva trae el último tag en sesión nueva;
  chequear que /reload-skills, hooks y registry/cargar se comporten igual que en
  el CLI · idea de MLL · ✅ RESUELTA (2026-06-15): la web carga el plugin desde el
  `.claude/settings.json` de cada repo; habilitado en los 10 repos del stack Lucky.
  No era el loader — era config por repo. /reload-skills SÍ existe (CLI y web).
- 2026-06-20 · gate global: reconfigurar `sys.stdin` a utf-8 (errors=replace) al
  inicio de crisol_gate.py · hoy en Windows un stdin con bytes UTF-8 crudos
  no-ASCII (rutas con tildes) puede dejar el gate inerte por fallo de decode
  (fail-open, SEGURO, pero el piso no muerde ahí) · hallado por el Verificador
  en la corrida v1.11.0 · mejora de robustez, NO bloqueante · idea parqueada
- 2026-06-21 · unificar el vocabulario de nombres de rol (`quién` de la matriz de
  veredictos): el dogfood usó `open_closed-verifier`/`scope_creep-verifier` mientras
  el roster §2 los nombra `design-verifier`/`scope-verifier`/`leak-verifier` · NO es
  cisma (el gate solo lee el veredicto `parts[1]`, nunca el quién) · hallado por el
  Verificador de Integración en la corrida del Crisol-endurecido · cosmético, no bloqueante
- 2026-06-21 · endurecer la detección de cierre más allá de `runState`: hoy un agente
  que nunca pone `runState: closing` deja una corrida ACTIVE colgada que solo caza la
  próxima brújula (enforcement de proceso, no del gate) · frontera declarada en ADR 0002 ·
  candidato kaizen
- 2026-06-21 · mecanizar progresivamente más reglas clase-H (híbridas) al gate
  determinista a medida que se vuelvan decidibles por código — baja el costo de
  verificación (token-free) y adelanta el FAIL · de la taxonomía M/J/H de la matriz
- 2026-06-28 · firma minisign del registry: diferida INDEFINIDA mientras sea solo-dev +
  loader `cargar` dormido — tratarla como DEFAULT (`--no-sign`), no como deuda. La firma
  protege integridad de cadena de suministro para TERCEROS que carguen el registry, no
  confidencialidad (por eso "repo público" no la exige). Reactivar solo si se abre a
  multi-IA / terceros que consuman el registry · decisión de MLL
- 2026-06-28 · registry.json NO valida contra registry.schema.json (pre-existente, sistémico):
  el schema marca `triggers` como required y `additionalProperties:false` sin declarar `url`,
  pero `forjar-release.sh` genera SIEMPRE `url` y NUNCA `triggers` → las 8 entradas fallan la
  validación. El schema description dice que la forja lo corre antes de firmar (defensa en
  profundidad), así que el schema desactualizado rompería ese gate. Decidir dirección: sincronizar
  el schema con el formato real (admitir `url`, `triggers` opcional) o que la forja emita `triggers`.
  Hallado por el review adversarial de bitacora (F21); afecta a toda la familia, NO solo bitacora ·
  candidato a corrida Crisol sobre forjar-release.sh + registry.schema.json
- 2026-06-29 · footer-bug "Ley viva": los footers de ~13 archivos (.md de skills + ADRs) usan
  `git ls-remote --tags` SIN remoto explícito → dentro de un repo consumidor resuelve contra SU
  origin, no contra lucky-skills, así que la red secundaria de detección de drift queda ciega.
  Fix = remoto explícito `https://github.com/mlandolfi90/lucky-skills.git` (como ya hace
  crisol/SKILL.md §6). Corrida SEPARADA: toca los mismos archivos que el re-sello concurrente ·
  hallado en la corrida autoUpdate
- 2026-06-29 · borde del Steward en `adoptar-crisol.sh`: inyecta `autoUpdate: true` sin validar
  que el `source` preexistente apunte a `mlandolfi90/lucky-skills`; si un repo tuviera una entrada
  `lucky-skills` apuntando a OTRO repo/fork, auto-seguir su main SÍ sería floating-de-tercero
  (viola PIN_TOTAL). Endurecimiento futuro: validar `source.repo == mlandolfi90/lucky-skills`
  antes de inyectar el flag · hallado en la corrida autoUpdate
- 2026-07-02 · endurecer `bitacora-lint.sh` (2 hallazgos menores del verificador fresco, ambos
  fail-closed hoy): (1) IDs con metacaracteres ERE fuera de la convención `[A-Z]+-[0-9]+` dan
  falso positivo en TÍTULO / huérfana falsa (escapar `$id` al interpolar en grep); (2) el pipe
  escapado `\|` de markdown en celdas del INDEX da "FILA malformada" (de facto prohíbe pipes en
  celdas — documentarlo o soportarlo). Ninguno produce falso verde · hallado en la corrida
  bitacora-lint
- 2026-07-02 · [ex GREP-001] patrón "grep ciego → pará y abrí el mapa (Key Files ≤5)": RETIRADO del
  catálogo por decisión del operador — sin evidencia real (0 usos en ningún ledger) y la acción
  prescribe un mapa que ningún repo tiene. Para revivirlo: crear el MAPA/Key Files en ≥1 repo y
  capturar el 1er uso real con sha. Texto completo en git history (v1.19.1 @ `02820ee`) · regla nueva:
  sin evidencia real no entra al catálogo
- 2026-07-02 · [ex GAP-001] patrón "incógnita con >2 ramas → spike timebox ANTES del Crisol": RETIRADO
  del catálogo — el patrón tiene espejo real (corrida S2d de auth-plane, 2026-06-21, spike PASS que
  cambió la decisión) pero la ENTRADA tuvo 0 usos. Para revivirlo: el próximo spike real que corra el
  patrón la destila de vuelta citando su evidencia. Texto completo en git history (v1.19.1 @
  `02820ee`) · regla nueva: sin evidencia real no entra al catálogo
- 2026-07-04 · [DECIDIDO — Vía A · plan completo: docs/refactor/_crisol/PLAN-i18n-costura.md] i18n /
  selector de idioma en TODOS los desarrollos, español de base. NO es una skill nueva (los 3 jueces del
  panel la rankearon última); su hogar es una extensión drop-in de `arquitectura` (reference + Router,
  como deploy) pero DIFERIDA a evidence-triggered (primer APPS real): crearla hoy con 0 usos =
  generalidad especulativa (lo que el repo ya castiga — GAP-001/GREP-001 retirados). NORMA VIVA que
  aterriza (no artefacto, sin ID §5, sin skill, sin tocar el gate):
  (1) DISCRIMINADOR — `RESPONSIVE` gatea DURO (UI rota en móvil = defecto de HOY) · `i18n` NO gatea (UI
  sin selector = capacidad-todavía-no-necesaria; gatearla = deuda especulativa contra el Crisol).
  (2) PATRÓN DE COSTURA — dispatch `(locale,key)→string` en el borde de presentación; español único
  locale poblado + fallback; i18n-ready pero MONOLINGÜE (seam con evidencia, cero idiomas precableados);
  agregar idioma después = soltar `locales/<lang>` + registrarlo, sin tocar el núcleo (Open/Closed).
  (3) "dejá la costura de idioma" = instancia de la regla COSTURA EXISTENTE (clase J), DIRECCIÓN DEL
  JUICIO fijada: juzga SOLO ubicación-cuando-el-plan-agrega-un-seam; la AUSENCIA de seam i18n es N/A,
  NUNCA FAIL (ningún plan de UI falla por no dejar costura i18n). Enforcement SUAVE: self-check advisory
  con guarda anti-promoción, JAMÁS checkbox en el conformidad-checklist binario ni ID en §5 (eso lo
  volvería fail-closed). DIFERIDO a su momento/ADR: reference+fila-Router en `arquitectura`, componente
  drop-in (i18next), señal en la brújula, language-pack pre-traducido de prosa (exige separar SEALED de
  HASHES), skill `idioma`. · MLL (plan Crisol 21-agentes, 2026-07-04)
- 2026-07-04 · DEUDA DE FIRMA ACTUAL (no de i18n): falta `.gitattributes` — `forjar-release.sh:256`
  (`sha256_lf`) lo asume presente para servir el raw en LF byte-idéntico; sin él, la paridad LF del raw
  que consume `cargar` es frágil HOY (UTF-8 multibyte), no solo el futuro language-pack. Saldar como fix
  de firma INDEPENDIENTE (definir primero qué normaliza el `.gitattributes` antes de crearlo) · hallado
  en el plan i18n · ✅ RESUELTA 2026-07-04 (commit 6da5333: `.gitattributes` EOL→LF + INDEX.md limpio,
  bajo Crisol Tier Completo; verificador probó 9/9 hashes firmados == registry, sin re-forja)
- 2026-07-05 · [corrida SOLID] adoptar-crisol.sh: (1) `json.load` del settings.json sin try/except (paso 1
  y 3b) — un JSON malformado muere con traceback crudo en vez de mensaje amable; (2) el guard canónico de
  `source.repo` compara exacto (`mlandolfi90/lucky-skills`) — variantes legítimas (capitalización, `.git`)
  caen al camino fail-closed y omiten autoUpdate; decidir si normalizar · hallado por el carril F2
- 2026-07-05 · [corrida SOLID] shift-left de `INTERFACE_SEGREGATION` a las reglas de PLAN del Steward
  (§3.6/§4-paso-4): una interfaz con ≥2 clientes y métodos sin usar ES plan-decidible; `LISKOV` NO (contrato
  semántico exige la impl real, fase-diff) · propuesto por el carril F3
- 2026-07-05 · [corrida SOLID] armonizar `auditor-checklist.md` §B: los ítems viejos [OPEN_CLOSED]/
  [ATOMICIDAD]/[COSTURA] re-enuncian el texto de la regla; los 2 nuevos son referencia-pura a §2/§5 —
  migrar los 3 viejos a referencia-only cierra el drift de fuente única · hallado por el carril F3
- 2026-07-05 · [corrida SOLID] el enforcer NO parsea el formato legado `## RUN`/`STATUS:` sin `- ` (el gate
  sí): con corrida legada activa el gate permite y el enforcer bloquea — divergencia fail-closed (no abre
  de más) pero drift real entre guardianes; + matiz: exclusión `docs/` por glob (enforcer) vs primer
  segmento (gate) podría diferir con rutas raras · hallado por el carril F1
- 2026-07-05 · [corrida SOLID] brujula/SKILL.md:44 (señal "ley atrasada", body no-footer) usa `git
  ls-remote --tags` pelado — mismo bug del footer-fix F6, quedó fuera del carril (scope=footers); una línea
  en corrida futura · hallado por el carril F6
- 2026-07-05 · [corrida SOLID] templates de `arquitectura` inconsistentes en footer: `auditoria-solid.md`
  nace con footer Ley-viva, `estructura.md`/`conformidad-checklist.md` no tienen — decidir si homogeneizar ·
  + candidata: helper de ruteo para el paso "Alimentá" de la auditoría (el depósito seguiría siendo humano/
  corrida, solo baja la fricción de copia) · hallado por el carril F4
- 2026-07-05 · [corrida SOLID] lint de pipes intra-celda: hoy solo se caza la forma escapada `\|` (el pipe
  crudo es indistinguible del delimitador); un markdown-lint podría exigir la entidad HTML en toda celda ·
  hallado por el carril F8
- 2026-07-05 · [corrida SOLID · verificadores] higiene de test-enforcer.sh (pre-existente, NO de esta
  corrida): las invocaciones FO-1/FO-3/FO-4 y la de cache llaman a $GATE sin la guarda have_gate → en
  contenedor fresco sin gate desplegado dan 3 FAIL espurios (17/3) en vez de skip; el override
  CRISOL_GATE_OVERRIDE (documentado en el header) da el 69/0 legítimo — 3 verificadores frescos tropezaron
  con lo mismo independientemente. Fix: guardar esas 4 llamadas con have_gate · hallado en la verificación
- 2026-07-05 · [corrida SOLID · verificadores] paridad de rutas/extensiones EXENTAS entre guardianes
  (.mdx/.markdown/.rst/docs//.claude/) queda asserted-por-comentario: el fixture prueba la paridad de la
  lista de CÓDIGO (grupo E) pero no extrae/compara las listas de exención — candidato a grupo E2 ·
  hallado por el design-verifier
- 2026-07-05 · [pase de prosa] ley/SKILL.md paso 6b usa `python` pelado (2×: el `python -c` del resolve
  de installPath y el heredoc de actualización del JSON) — MISMO bug que F2 arregló en adoptar-crisol.sh;
  en Linux-solo-python3 el refresco de cache muere. Fix chico (resolver python3||python), corrida aparte:
  esta corrida es prosa-only por alcance declarado · hallado en el pase quirúrgico de prosa · ✅ RESUELTA 2026-07-05 (corrida fast-path propia, mismo release v1.26.0)
- 2026-07-04 · auditar si REALMENTE aplicamos SOLID en la construcción de sistemas (skills + apps de los
  repos), no solo en la teoría. Contexto que AHORRA trabajo: el Crisol YA encarna 4 de los 5 como reglas
  de Diseño (§2) — `OPEN_CLOSED` (explícito) · `ATOMICIDAD` ≈ Single-Responsibility · `COSTURA` ≈
  Dependency-Inversion (la costura donde el sistema varía) · `CONFORMIDAD` hexagonal (deps hacia adentro,
  núcleo sin I/O) ≈ DIP+ISP. GAP a chequear: Liskov (sustituibilidad) e Interface-Segregation no tienen
  regla propia; y SOBRE TODO si el CÓDIGO real de cada repo cumple, no solo el reglamento (el Crisol
  verifica el diff de cada corrida, no hace auditoría retroactiva del código ya existente). Candidata a
  corrida de AUDITORÍA read-only por repo (mapear violaciones SOLID vivas) o a enmienda del
  `conformidad-checklist`. · idea de MLL
- 2026-07-09 · pin-por-commit REAL para cargar (v2): hoy la forja corre PRE-commit, así que el campo
  `commit` del registry apunta al HEAD anterior al commit del release → el pin efectivo es por TAG
  (documentado en ADR 0009). Idea v2: forja en dos pasadas (commit del release primero, registry después
  apuntando a ese sha, amend controlado) o registry post-commit en un artefacto separado — cerraría el
  vector tag-movido sin necesitar firma. · surgió del retiro de minisign (corrida 2026-07-09)
- 2026-07-09 · limpiar prosa stale de la era pre-/reload-plugins: el echo final de forjar-release.sh
  ("paso 5: corregir README L19") y la nota en cargar/references/detectar-runtime.md sobre el mismo
  README L19 — el README ya está corregido hace rato; ambos avisos son ruido. Fix de 2 líneas, corrida
  aparte (fuera del alcance del retiro de minisign). · hallado en la corrida 2026-07-09
- 2026-07-09 · paridad de guardianes en el borde "repo git SIN commit inicial" (HEAD irresoluble): el
  gate python hace fail-open (permite: "no podemos saber el branch") y el enforcer bash usa el literal
  `HEAD` como branch y bloquea — asimetría pre-existente, NO introducida por el lote ECC (el verificador
  fresco la reprodujo en toy repo). Fix chico: decidir UNA semántica (sugerido: fail-open en ambos, es
  el espíritu del gate) + caso nuevo en test-enforcer. Corrida aparte. · cazada por verificador-fresco 2026-07-09

- 2026-07-09 · REPENSAR el planteo del parking de ideas: hoy conviven ideas GLOBALES (~/.claude/IDEAS-GLOBAL.md) e ideas DEL REPO/PROYECTO (docs/IDEAS.md) como fallback accidental, no como diseño — convertir los dos ámbitos en concepto de primera clase (¿dónde nace cada una, cómo se consultan juntas, cuándo asciende una global a un repo?). Decisión del operador: parqueada, NO entrar todavía. · orden de MLL 2026-07-09
- 2026-07-09 · HIGIENE DE MÁQUINA: maquina-scan cazó un plugin legacy `crisol-enforcer` en ~/.claude con `python` pelado no-portable (mismo bug de DRIFT-007) — es un cableado viejo/redundante del gate, distinto del lucky@lucky-skills activo que ya migramos. Decidir: borrar el plugin legacy, o migrar su hooks.json al comando portable. NO es cambio de repo (es config de la máquina del operador). · hallado por la 1ra corrida de maquina-scan
- 2026-07-09 · maquina-scan v2: sumar heurística de MCP más fina (no solo "hay config" → listar servidores y flaggear los que piden red amplia/exec), y correrlo desde crisol-pulso/heartbeat como los otros gates. · surgió al forjar maquina-scan
- 2026-07-10 · MCP para vaults de hotfix: hoy el vault vive en el repo (docs/refactor/_hotfix/); la idea
  es un MCP que los gestione fuera del repo (sobrevive rollbacks/clones frescos, consulta cross-repo,
  marca de cosecha centralizada). Esperar a que el carril hotfix pruebe su valor en uso real primero. · idea de MLL (al diseñar la skill hotfix)
- 2026-07-11 · limpiar la inconsistencia interna de DRIFT-009 (ejemplo etch-mode): L5 dice "pastilla REC = etch-mode" pero L14 dice que gatear por etch-mode hacía reaparecer el bug POR la pastilla REC — no cierra si pastilla=etch-mode; el operador no reconoció etch-mode al revisarlo. Aterrizar la topología real de HOT-MIC y corregir la entrada. · surgió al usar DRIFT-009 de molde en la corrida hotfix anti-círculo (ADR 0014)
- 2026-07-12 · [APAGADA / no activa — hoy queda md plano] proyección SQLite consultable para el RUN-LEDGER (y
  catálogos): un único .db GENERADO desde el md (que sigue siendo la fuente de verdad auditable/git-diffable,
  por ADR 0015). Da SQL para analítica del ledger (fast-path vs completo, corridas por skill…) y reserva
  `sqlite-vec` para búsqueda semántica APAGADO. Gatillo para prenderlo: escala del corpus + un miss de recall
  REAL que se sienta — NO la disponibilidad tecnológica. Restricciones duras: nunca un gate (embeddings
  probabilísticos vs Crisol determinístico/fail-closed) → siempre lado consejo; el .db es proyección
  regenerable, JAMÁS la fuente de verdad (blob binario, no auditable). Relacionado: ADR 0015 (espejo saber),
  substrato lucky-saber. · discusión md→estructurado + vectorial (2026-07-12)

- 2026-07-16 · Refactorizar la familia de skills lucky como ÁRBOL ÚNICO: un tronco común del plugin que rutea ("sabe llamarse según lo que necesite") y las 11 skills colgando como ramas; cada skill = tronco estable + ramas que se AGREGAN a medida que el aprendizaje crece (Open/Closed sobre la ley; rama nueva = archivo nuevo + línea en el índice, jamás reescribir el tronco). Estructura de lectura IDEMPOTENTE: fuente única por enunciado (cero duplicación), carga determinista (tronco siempre, ramas on-demand/pull), y scripts (forja/carga) re-ejecutables N veces sin efectos acumulados. Integración de ramas: cosecha (bitácora/saber propone, humano endosa) + manual según el caso. SIN cambiar comportamiento de las skills · corrida Crisol tier completo pendiente de permiso; TARGET pc-local; MODEL fable (uniforme)
- 2026-07-16 · Escalera de ciclos de calidad ADITIVA: microfix → hotfix → corrida Crisol — dividir los pasos en etapas agregables; el flujo crece y va cumpliendo etapas, cada nivel agrega ceremonia solo si el caso lo pide · debate refactor árbol
- 2026-07-16 · Decisiones CONVOCABLES como registro: cuando el flujo necesita juicio humano se crea una decision PROPUESTA que se le presenta al usuario; si el usuario la deprecа/rechaza, el estado se refleja en el registro (RECHAZADA/SUPERSEDIDA) · debate refactor árbol
- 2026-07-16 · Regla dura de entorno: JAMÁS empezar a codear en pc-local — el fix nace en el entorno caliente (dev) y promociona dev→test→prod; hoy a veces se arranca en la PC local y no tiene sentido → reforzar enforcement · debate refactor árbol
- 2026-07-16 · Definir AGENTES como registros canónicos: los guardianes (verificadores/steward/auditores) hoy reciben directivas improvisadas por el líder en cada corrida — no determinista, depende de la temperatura del modelo; sus prompts/checklists deben ser archivos pineados y versionados con la ley que se cargan TAL CUAL al spawnear (el rol se lee, no se redacta) · debate refactor árbol
- 2026-07-16 · Refinamiento agentes canónicos (aprobado en debate): evolucionables (fila LIVE→SUPERSEDED, schema versionado) y composición DECLARADA — frontmatter `delega: [agente:x]` que el orquestador resuelve al spawnear (los subagentes no anidan en el harness); agregar sub-verificador = 1 línea en delega · debate refactor árbol
- 2026-07-16 · Definición del MICROFIX (peldaño 1 de la escalera de ciclos): sonda mínima que solo busca corregir UN comportamiento — tocar código en UNA parte específica y observar si el cambio es favorable; alcance de un solo punto, veredicto favorable/no-favorable; si revela profundidad escala a hotfix llevándose su registro · debate refactor árbol
- 2026-07-16 · Definición del HOTFIX (peldaño 2 de la escalera): investigar A FONDO la corrección del bug en específico hasta encontrar la forma de corrección — encontrar y corregir la falla para tener claro el camino SIN gastar corridas locas; la corrida Crisol llega recién con la solución ya clara (formaliza, no explora) · debate refactor árbol
- 2026-07-16 · FEATURES como registro de primera clase (hoy se abusa de IDEAS.md y no debe ser así): una feature tiene nacimiento, funcionalidad, de qué evolucionó, qué se hizo/intentó y qué funcionó, y si aún no se implementa; puede dividirse en escaleras y CRECER por sub-features sin cerrar (ej: sección "settings" de una web que después recibe más cosas adentro). Requiere skill propia (/feature) + AGENTE curador canónico que mantenga el árbol de features · debate refactor árbol
- 2026-07-16 · Refinamientos de la escalera (aprobados en debate): (1) toda corrección ARRANCA como microfix y el flujo PREGUNTA hasta qué escalón llega, salvo que el operador indique el tope de entrada; (2) prohibido saltar escalones — escalada secuencial, cada peldaño lleva los refs del anterior ("¿quién tiene piernas tan grandes?"); (3) TARGET obligatorio en TODO peldaño pero el env legal varía por peldaño/caso (microfix local solo en casos especiales específicos; hotfix en dev; fast-path puede ser producción si es importante) — siempre declarado, jamás asumido · debate refactor árbol
- 2026-07-16 · WORKSPACE del agente sin patrón único (evidencia en la carpeta contenedora "Proyecto Afinamiento 1": screenshots de playwright sueltos en la raíz, .pytest_cache en la raíz contenedora, fix.ps1/audit.ps1 huérfanos, HANDOFF/PLAN/REPORTE-*.md sin hogar, carpetas "Nueva carpeta"/"enjambre"): definir DÓNDE ejecuta y guarda el agente cada clase de artefacto — tests desde la raíz del repo, evidencia visual en carpeta declarada del repo o scratchpad temporal, scripts en repo/scripts, reportes como registros; PROHIBIDO escribir en la carpeta contenedora — todo artefacto del agente tiene hogar declarado (extensión de registros.yaml al workspace) · debate refactor árbol
- 2026-07-16 · CONCEJOS (paneles multi-agente) como registro indexable: cuando se lanza un concejo de varios debatientes (diseños independientes + jueces) el veredicto es ORO PURO — el estudio de un caso desde varios ángulos — pero hoy queda en un archivo temporal de sesión que se pierde; debe ser tabla propia (docs/concejos/): {pregunta, ángulos/debatientes, scores por juez, ganador, injertos, riesgos, refs a la corrida/feature/decision que alimentó}; el orquestador lo archiva al completar el panel · debate refactor árbol
- 2026-07-16 · Concejos — directiva del operador: el panel de hoy (estructura-docs-DB, en temp de sesión) NO se rescata; el archivado automático de veredictos rige para los PRÓXIMOS concejos desde que el refactor esté vivo (coherente con doctrina "historia no se convierte preventivamente") · debate refactor árbol
- 2026-07-16 · PLAN DE ARCHIVOS canónico por repo (sembrado por adoptar-crisol, complemento del workspace): <código hexagonal> + tests/ (corren desde la raíz) + e2e/{artefactos/ evidencia referenciada por refs, .tmp/ gitignored borrable} + scripts/ con dueño + docs/{registros.yaml, decisions, crisol/runs, hotfixs, features, concejos, IDEAS.md}; evidencia efímera → scratchpad de sesión fuera del repo. Evidencia: Lucky-Debugger/e2e ya intuyó el patrón (artefactos/) pero ad-hoc y con .tmp sucio · debate refactor árbol
- 2026-07-16 · DOCUMENTACIÓN por software para TRES audiencias: cada soft debe tener su documentacion/help/guia/manual — (1) para el USER (cómo se usa), (2) para el DESARROLLADOR futuro que no recuerde cómo funcionaba el sistema, (3) para el LLM que entre al repo; método Diátaxis (tutorial/how-to/reference/explanation) + CLAUDE.md-AGENTS.md para el agente; posible gate: una feature no llega a VIVA sin su doc (mismo patrón que el gate de crédito técnico exige ADR) · debate refactor árbol
- 2026-07-16 · VISIBILIDAD producto vs taller (cuestión del operador: al liberar proyectos no debe irse la retroalimentación — como la industria entrega el modelo pero no el paso a paso del entrenamiento): registros.yaml gana columna visibilidad: producto (docs/manual, docs/sistema, README) | taller (corridas, hotfixs, ideas, concejos, señales); DOCTRINA DE LIBERACIÓN: liberar = EXPORTAR copia limpia generada por la forja con historial nuevo (solo visibilidad producto) — JAMÁS publicar el repo de trabajo porque el historial git cuenta el taller entero · debate refactor árbol
- 2026-07-16 · Directiva de liberación confirmada: los git actuales son historial importante de evolución y autoaprendizaje del operador (taller); liberar = repo público NUEVO con solo la versión utilizable, vía técnica de industria (exportación limpia). NUEVO requisito: la documentación/manuales (producto) debe poder VERSE en la app/web/etc — docs/manual/ es la fuente única (docs-as-code) y la app la RENDERIZA (sección help/docs que lee el mismo markdown; jamás texto duplicado hardcodeado en la UI) · debate refactor árbol
- 2026-07-16 · AGENTE DOCUMENTADOR con equipo (nombre tentativo del operador: "Manualizador", por definir): agente canónico con nombre y rol definidos en la skill y en su carpeta (fila de la tabla agente, con delega: para su equipo); mantiene docs/manual y docs/sistema renderizables en la app. GATILLOS ESTRICTOS — solo se llama cuando: (1) una feature avanza a estable/VIVA, o (2) hay modificación de comportamiento y se le dice explícitamente que aplique; JAMÁS documenta en caliente trabajo inestable · debate refactor árbol
- 2026-07-16 · Afinaciones aprobadas en debate: (1) TABLERO del operador — proyección generada "qué está abierto y qué espera mi juicio" como bandeja de entrada de sesión; (2) TELEMETRÍA de ramas — tick por carga (saber_telemetria), la cosecha poda ley muerta con evidencia; (3) skill NACER — bootstrap completo de repo nuevo (esqueleto por tier + docs/tablas + registros.yaml + CLAUDE.md + adopción Crisol), aplicando lo óptimo de la industria; (4) EVALS de la ley EXTENDIDOS — batería al forjar que verifica que el árbol rutea (síntoma→rama correcta) y el determinismo de agentes canónicos; (5) LEAK-SCAN extendido a las tablas nuevas (runs, concejos, hotfixs, features) · debate refactor árbol

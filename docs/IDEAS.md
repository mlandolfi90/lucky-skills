# IDEAS — parking lot (formato: YYYY-MM-DD · idea · contexto-sin-secretos)

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
- 2026-07-04 · SELECTOR DE IDIOMA + traducción integrada como capacidad POR DEFECTO en TODOS nuestros
  desarrollos (no solo las skills): como el "Responsive obligatorio" del Crisol pero para idioma — toda
  app/UI/panel que creemos trae selector de idioma + capa de traducción, SIEMPRE, con el español como
  base. Encaje natural en la ley: REGLA nueva del Crisol paralela a `RESPONSIVE` ("i18n obligatorio":
  UI sin selector de idioma → FAIL) + invariante de la skill `arquitectura` + fila en
  `conformidad-checklist`; el verificador la chequea igual que responsive. Sub-caso: la propia familia
  de skills (prosa markdown) en varios idiomas — el LLM ya opera en cualquier idioma, el tema es
  legibilidad humana del archivo → language-pack PRE-traducido por locale, cargado on-demand por
  `cargar`, cada uno firmado aparte en el registry (una traducción cambia el `sha256`; el español
  canónico sigue siendo la fuente firmada). Ejes de diseño: build-time firmable vs runtime LLM al vuelo;
  servicio tipo Crowdin vs el propio LLM. Corrida grande con ADR · idea de MLL (refinada 2026-07-04)

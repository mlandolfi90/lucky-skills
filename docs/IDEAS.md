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

---
id: adr:0020
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-ecosistema-features-migrar, adr:0016, adr:0017, adr:0019]
---

# 0020 — Ecosistema: features de primera clase, Manualizador, /migrar, evals y métricas

## Contexto

Cierre del programa del debate 2026-07-16. Dolores restantes del operador:
(a) "a veces se me ocurre algo que quiero que TENGA el proyecto — no es una
idea de parking: debe tener su nacimiento, su funcionalidad, de qué
evolucionó, qué se intentó, y puede CRECER sin cerrar" (hoy se abusa de
IDEAS.md); (b) cada soft necesita documentación para TRES audiencias (user,
dev futuro, LLM) visible EN la app, mantenida por un agente con gatillos
estrictos; (c) los repos que no nacieron bajo la ley 2.0 necesitan un
retrofit ordenado (la evidencia: screenshots y `.pytest_cache` en la carpeta
contenedora, `HANDOFF-*.md` sin hogar); (d) sin evals ni métricas, el refactor
"se siente mejor" y nada más (M1-M9 aprobadas con baseline pre-play).

## Decisión

1. **Features de primera clase** (skill `feature`, tabla ya declarada):
   una feature nace `PROPUESTA` (a menudo promovida desde una idea madura —
   la idea pasa a estado `PROMOVIDA` en su línea), registra `origen`,
   `intentos` (qué se hizo/probó y qué funcionó) y avanza
   `EN-DISENIO → EN-CONSTRUCCION → VIVA` — **jamás "cierra"**: crece por
   sub-features (`padre: feature:<id>`), el árbol otra vez. **Gate de doc**:
   no llega a `VIVA` sin su documentación (`doc:` apuntando a
   `docs/manual/…`) — mismo jidoka que el gate de crédito técnico.
2. **Documentación de tres audiencias** — user: `docs/manual/` (la app la
   RENDERIZA desde esta fuente única — jamás textos duplicados en la UI);
   dev futuro: `docs/sistema/` + ADRs; LLM: `CLAUDE.md`. Método Diátaxis
   (tipos separados, crecimiento incremental). Visibilidad: `producto`.
3. **Agente canónico `manualizador`** (nombre elegido por el operador):
   mantiene manual y sistema. **Gatillos ESTRICTOS**: (a) una feature pasa a
   `VIVA`, o (b) cambio de comportamiento + orden explícita del operador.
   Documentar trabajo inestable = fabricar drift → prohibido.
4. **Retrofit de la flota** (skill `migrar` + agente canónico
   `migrar-clasificador`): para repos pre-2.0 — inventariar el desorden real,
   CLASIFICAR cada artefacto contra `registros.yaml` (¿fila? ¿narrativa?
   ¿config? ¿basura?), proponer el mapeo completo y **esperar el ENDOSO del
   operador** (decisión convocable, ADR 0019 §2) antes de mover NADA;
   monolitos se congelan verbatim (jamás se convierten); termina con
   `registros-lint` en 0. Complementa `adoptar-crisol.sh`: la adopción
   SIEMBRA lo nuevo, la migración ORDENA lo viejo.
5. **Evals de ruteo mecánicos en la forja** (`test-ruteo.sh`, fail-closed):
   todo tronco declara disparadores; toda rama estable tiene gatillo no
   vacío, único dentro de su skill, y de longitud útil. Los evals
   LLM-conducidos (¿el agente elige la rama correcta ante el síntoma X? —
   harness promptfoo pineado) quedan como deuda declarada.
6. **Métricas del programa** (`scripts/metricas.py`, report-only): mide
   M1 (troncos ≤400 — citación), M2 (corrida ≤60 líneas de frontmatter+prosa),
   M3 (huérfanos = lint), M5 (ruteo), M6 (idempotencia), M7 (paridad),
   M8 (sellos), M9 (presupuesto de contexto por activación: tronco+ramas).
   M4 (tokens de arranque) se mide por sesión — N/D desde script.

## Consecuencias

- "Quiero que el proyecto tenga X" deja de perderse en el parking: tiene
  fila, historia, intentos y descendencia — y no miente: sin doc no está VIVA.
- La flota vieja tiene camino de retorno a la ley sin big-bang y sin que un
  agente mueva archivos que el operador no endosó.
- La forja gana su primer eval de ruteo: el árbol no solo crece — se verifica
  que SIGA siendo navegable.
- Deuda declarada: evals LLM de ruteo (promptfoo pineado); render real del
  manual en cada app (por-proyecto, cuando exista UI); M4 por sesión; el
  AGENTE CURADOR del árbol de features (detecta estancadas, propone promover
  ideas maduras — captura del operador) entra cuando la tabla tenga filas
  reales que curar; medición no-op de adoptar/forja vive en las suites, no
  en metricas.py.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).**

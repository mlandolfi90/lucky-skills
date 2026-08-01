# El Taller

Suite portable de gobernanza para agentes de programación: **28 skills**
selladas, cada una en su cajón, cada una con su versión.

El nombre viene de su filosofía: un mecánico tiene el taller lleno de
herramientas, pero no carga con todas al meterse debajo del auto — agarra
la que el momento pide. Acá igual: contratos de una página, cargados solo
cuando se necesitan, con el criterio siempre en manos de quien trabaja.

## Qué hay

- `skills/` — las 28, cada una con su `SKILL.md` (contrato) y `manifest.env`
  (versión SemVer + dependencias). Selladas a 1.0.0 en tags anotados
  `skill-<id>-v1.0.0`.
- `adapters/` — adaptador de referencia (Python determinista) y empaquetado
  por harness: Claude Code, Codex, Claude.ai — con degradación declarada,
  jamás fingida.
- `docs/concepts/` — el vocabulario canónico, un concepto por página.
  Para adoptar en un repo: [paquetes de adopción](docs/concepts/adoption-packs.md).
- `tests/` — 168 pruebas de conformidad. `python -m pytest -q` y
  `python adapters/reference_python/run_validate_suite.py` son la verdad.

## Las tres reglas de la casa

1. **Hipótesis libres, consecuencias firmadas** — experimentar no pide
   permiso; lo irreversible exige TARGET confirmado y un plan cuyo hash
   firma el humano. Lo que la compuerta no muestra, no queda autorizado.
2. **Evidencia o silencio** — sin evidencia contrastable no hay veredicto:
   hay `UNKNOWN`, declarado. El verde que no puede probarse no es verde.
3. **Cada cosa en su cajón** — una responsabilidad por skill; si la frase
   necesita un "y", son dos skills. La madrina lo vigila desde la cuna.

## Generaciones

La familia v2 (la "ley": tags `v2.x`) vive en la rama [`v2`](../../tree/v2),
congelada en v2.11.0 rumbo al retiro. El Taller no la reemplaza línea por
línea: la destila — su disciplina quedó en contratos que se verifican solos.

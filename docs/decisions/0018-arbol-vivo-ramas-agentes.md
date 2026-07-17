---
id: adr:0018
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-16
supersede: null
superseded_by: null
refs: [corrida:2026-07-16-ramas-agentes-canonicos, adr:0016, adr:0017]
---

# 0018 — El árbol vivo: ramas con cuarentena y guardianes canónicos

## Contexto

ADR 0016 §5 decretó que el aprendizaje entra como RAMA sin reescribir el
tronco, pero el mecanismo quedó sin estrenar: dos corridas seguidas ENGORDARON
el tronco de crisol (562→589 líneas) porque no había otra vía. Y los
guardianes del Crisol se spawnean con prompts que el líder REDACTA en cada
corrida — el operador lo señaló como fuente de no-determinismo: "no siempre
les das las mismas directivas; dependes de tu temperatura". La investigación
del debate (2026-07-16) documentó además el vector de seguridad: contenido
que se auto-carga al contexto del agente por gatillo es superficie de prompt
injection — la defensa robusta es provenance + endoso humano, no detección.

## Decisión

1. **Mecanismo de ramas**: cada skill puede tener `ramas/NNN-slug.md` (fila:
   `schema: rama/1`; columnas `gatillo` — el síntoma que la carga —, `canal`,
   `origen`, `ultima_validacion`, estados `PROPUESTA | LIVE | EN_DUDA |
   SUPERSEDIDA`). El tronco lleva UN bloque
   `<!-- RAMAS:BEGIN -->…<!-- RAMAS:END -->` que `scripts/proyectar.py`
   regenera desde las filas (patrón blockinfile: se reemplaza entre
   marcadores, byte-determinista). El agente carga el tronco siempre y abre
   SOLO la rama cuyo gatillo matchea (lazy, una indirección).
2. **Cuarentena (canal `propuesta` → `estable`)**: toda rama nace
   `canal: propuesta` y NO entra al índice del tronco — no rutea — hasta que
   el operador la promueve a `estable` (endoso explícito, mismo espíritu que
   CANDIDATE→LIVE de la bitácora). Excepción: una rama EXTRAÍDA del tronco
   (ley ya endosada que solo se muda) nace `estable` — mover no es proponer.
   Contenido derivado de fuentes externas jamás porta instrucciones
   ejecutables (`trust: untrusted` si aplica).
3. **Corrección de rama = supersede**: una rama equivocada pasa a `EN_DUDA`
   (juicio del operador) o es reemplazada por una rama nueva
   (`superseded_by`); jamás se reescribe una rama LIVE.
4. **Guardianes canónicos**: los roles de verificación del Crisol viven como
   archivos en `plugins/lucky/agents/` — frontmatter del harness
   (`name`/`description`/`tools`) + columnas de fila (`id`, `schema:
   agente/1`, `estado LIVE|SUPERSEDED`, `dictamina:` reglas §5, `delega:`
   sub-agentes) + cuerpo = **el prompt canónico**. El líder spawnea por
   nombre y el prompt SE LEE, no se redacta — misma directiva en cada
   corrida, cero temperatura en el mandato. **El `delega:` lo resuelve el
   ORQUESTADOR (líder) al spawnear** — los subagentes no anidan; agregar un
   sub-verificador = una línea en `delega:` del archivo. Ante divergencia
   entre la tabla del roster (tronco) y el archivo canónico, el `dictamina:`
   del archivo MANDA (fuente única). Evolución = archivo nuevo que
   supersede (como los ADRs). Viajan sellados con la familia (la forja los
   re-sella, junto con las ramas — ley que rutea al contexto viaja sellada);
   su hash en registry.json queda como deuda declarada.
5. **El tronco solo adelgaza o queda igual**: con el mecanismo vivo, contenido
   condicional del tronco (reglas que aplican solo a ciertos diffs) se extrae
   a ramas con gatillo; el techo de 400 (citación, ADR 0008) empuja en esa
   dirección en cada corrida que toque un tronco citado.

## Consecuencias

- El aprendizaje nuevo cuesta un archivo + una línea generada — no una
  reescritura de tronco bajo corrida completa.
- Nada rutea al contexto de un agente sin firma del operador (cuarentena) —
  cierra el vector de envenenamiento por rama.
- Los veredictos de guardianes se vuelven comparables entre corridas (mismo
  prompt → misma vara); la regresión de un prompt es un diff visible.
- Deuda declarada: hash de `agents/` en registry.json; telemetría de uso de
  ramas (T3) alimentará la poda de gatillos muertos.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.5.0` (cache local, NO la ley).**

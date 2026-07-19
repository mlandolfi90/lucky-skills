---
id: adr:0024
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-18
supersede: null
superseded_by: null
refs: [corrida:2026-07-18-cosecha-agent-skills]
---

# 0024 — El refactor de costura declara qué DESAPARECE

## Contexto

El caso legal (b) de tocar lo estable (crisol §2 «Cuando tocar lo estable es
inevitable») solo exigía **"verde antes y después"** — la prueba de que el
refactor que abre la costura NO rompe comportamiento. Pero verde antes/después
prueba no-romper, **no simplificar**: un refactor que parte 600 líneas en
3×200 pasaba el gate limpio sin haber eliminado ninguna rama, modo, capa ni
acoplamiento. La corrida-2 (la extensión) entraba entonces por una **costura
inexistente** — el sistema no varió, solo se movió de lugar. Relocalización
disfrazada de refactor, con el verde como coartada.

Origen: cosecha de `github.com/addyosmani/agent-skills` (skill
`code-review-and-quality`). Adaptada al Crisol: se tomó la **declaración
nominal** de lo que se elimina, resoluble mecánicamente contra el diff, y se
**DESCARTÓ** el conteo de conceptos de la fuente (juicio no determinista, choca
con el eje «objetivo» del Crisol).

## Decisión

1. **`DESAPARECE: <nombre>` obligatorio en el caso (b)**: el refactor de costura
   declara POR NOMBRE la rama, modo, capa, acoplamiento o duplicación que
   elimina, en el plan/ledger de su corrida.
2. **Resolución mecánica doble** por el `design-verifier` contra el **diff de
   resta**: el nombre declarado debe (a) estar en líneas borradas (`-`) Y (b) no
   seguir existiendo en el árbol post-diff. Las dos condiciones o no hubo
   eliminación.
3. **FAIL = relocalización**: `DESAPARECE` ausente/vacío, o nombre que sigue en
   el árbol (se movió, no se borró) → no es refactor de costura → `FAIL`
   (`COSTURA`). El ID de matriz `COSTURA` no cambia: no hay contrato nuevo de
   matriz.

**Límite declarado**: el **renombre disfrazado** (borrar `A`, re-crear `B`
idéntico) queda FUERA del alcance mecánico — cae al juicio OCP/generalidad del
`design-verifier`. NO se intentará cerrar con heurística de similitud (sería
juicio no determinista, la misma trampa que el conteo de conceptos que se
descartó).

## Consecuencias

- **Fricción intencional** en los refactors que tocan estable bajo (b): ahora
  hay que declarar y probar qué se eliminó, no solo que no se rompió. Es el
  costo de que la costura sea real.
- **Corolario "borrar antes que pulir"** en los anti-patrones de la skill
  `arquitectura` (sección «Refactor / costura», fila `Reubicar en vez de
  borrar`): el catálogo transversal lo referencia por nombre.
- **Sin cambio de contrato de matriz**: el ID `COSTURA` es el mismo; se le suma
  una condición resoluble, no una regla nueva con ID propio.
- **Considerado y descartado a propósito**: el conteo de conceptos de la fuente
  (addyosmani/agent-skills) — juicio no determinista, incompatible con el eje
  objetivo del Crisol. Se tomó solo la parte mecanizable (declaración nominal +
  diff de resta).

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.9.0` (cache local, NO la ley).**

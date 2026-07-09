# GUÍA-SKILLS — doctrina de autoría de la familia lucky

> Destilada de ECC `SKILL-DEVELOPMENT-GUIDE.md` (919 líneas, 278 skills en
> producción) + checklist de su CONTRIBUTING, traducida y adaptada a la doctrina
> lucky (2026-07-09, corrida "absorción ECC lote 1"). La consulta el autor de
> una skill nueva y el reviewer de una corrida que toque SKILL.md.

## Tamaño y alcance

1. **200–500 líneas típico; 800 es el techo duro.** Pasado el techo: partir o
   mover a `references/`.
   - **Válvula lucky (precedente v1.28.0):** una skill/ley puede ser
     *larga-legítima* si es un cuerpo normativo de archivo único ya compuesto
     en secciones SRP (dictamen del design-verifier, citado por nombre en la
     matriz — igual que ATOMICIDAD en código). No es excusa por defecto: es
     dictamen por corrida.
2. **Un solo dominio por skill.** `pytest-fixtures`, no `python-testing`;
   `nextjs-app-router`, no `nextjs`. Si el título necesita una "y", son dos
   skills.

## La `description` ES el trigger

3. Una `description` dice **cuándo** dispararse, no qué es la skill: verbos de
   acción + síntomas/frases del usuario + fronteras negativas ("NO usar
   para…"). Las skills lucky ya hacen esto — sostenerlo en toda skill nueva.
4. **String inline o folded (`>-`), JAMÁS bloque literal (`|`)** — los literales
   preservan newlines y rompen renderers/parseos planos.
5. El cuerpo abre con el equivalente de "cuándo activar": escenarios concretos
   observables, no categorías abstractas.

## Contenido: mostrar, no declamar

6. **Código copy-pasteable > prosa.** Malo: "manejá bien los errores". Bueno: el
   bloque con `try/catch` + chequeo + re-throw, y un "puntos clave" de 3 líneas.
7. **Anti-patrones SIEMPRE**, en pareja: `MAL:` y `BIEN:` lado a lado. Aprender
   qué NO hacer vale tanto como el patrón.
8. **Explicar el PORQUÉ** en una línea junto al qué (la regla sin racional se
   cumple menos — y el nivel adverso de /cumplimiento lo demuestra).
9. Herramientas de densidad: checklists `- [ ]`, árboles de decisión, tablas de
   convención. Bloques de código SIEMPRE con identificador de lenguaje.

## Progressive disclosure (raíz vs anexos)

10. **En la raíz (`SKILL.md`):** lo que el agente necesita SIEMPRE y de
    inmediato — método, reglas duras, disparadores.
11. **En `references/`:** el detalle profundo consultable por tarea (se carga
    bajo demanda — encaja con la carga progresiva de `cargar`).
12. **En `templates/` / `scripts/` / `tests/`:** artefactos ejecutables o
    copiables. Los ejemplos de código deben FUNCIONAR de verdad (compilar/
    correr), no pseudocódigo.
13. Regla de reparto: si una sección solo se lee "cuando toca X", es reference;
    si su ausencia cambia la conducta general del agente, es raíz.

## Anti-patrones de autoría

14. Vaguedad no accionable ("escribí buen código").
15. Prosa larga sin un solo bloque de código.
16. Alcance múltiple (tres dominios en una skill).
17. Teoría sin ejemplos, o ejemplos sin anti-patrón.
18. **Datos sensibles**: cero API keys/tokens/rutas absolutas (leak-scan lo
    caza, pero el autor no debería llegar ahí).

## Política de adaptación de terceros (espejo de la de ECC)

19. Se copia la **idea**, no la identidad del producto: renombrar a la
    superficie lucky, traducir al español, citar el origen en el encabezado.
20. Preferir mecanismo propio (hook/gate/script del repo) antes que sumar
    dependencia externa; jamás publicar una skill cuyo único valor sea
    "instalá este paquete no auditado".

## Checklist del autor (pre-corrida)

- [ ] Un dominio; título sin "y"
- [ ] `description` = cuándo dispararse + frontera negativa; folded, no literal
- [ ] Reglas duras arriba; detalle en `references/`
- [ ] ≥1 ejemplo real + ≥1 anti-patrón en pareja MAL/BIEN
- [ ] ≤500 líneas la raíz (o dictamen larga-legítima en la matriz)
- [ ] Cero secretos/rutas absolutas
- [ ] Sello Ley-viva al pie (la forja lo exige: exactamente 1 ancla)
- [ ] Si la conducta es crítica → escenario en `cumplimiento/escenarios/`

## Auditoría de tamaños (2026-07-09)

| SKILL.md | líneas | dictamen |
|---|---|---|
| crisol | 555+ | **larga-legítima** (cuerpo normativo único, precedente v1.28.0 sobre crisol_gate.py 671) — se re-dictamina por corrida |
| cargar | ~293 | OK |
| arquitectura | 179 | OK |
| ley | 146 | OK |
| bitacora | ~135 | OK |
| cumplimiento | ~110 | OK |
| brujula · management · diseno · idea | ≤107 | OK |

Conclusión de esta pasada: **ninguna skill exige compactación hoy**; el techo
recién muerde en crisol y tiene dictamen. La guía queda como gate de autoría
para lo que nazca.

---
id: adr:0025
schema: decision/1
tipo: decision
estado: ACEPTADA
creado: 2026-07-18
supersede: null
superseded_by: null
refs: [corrida:2026-07-18-cosecha-agent-skills]
---

# 0025 — Supuestos declarados del plan

## Contexto

El alcance o la premisa mal entendidos se cazaban recién en la verificación,
como `SCOPE_CREEP` — el Ingeniero ya había codeado sobre una premisa falsa y el
`FAIL` **quemaba una iteración del techo** (3). El error nacía arriba (el plan
malinterpretó el problema) pero se detectaba abajo, con el costo máximo.

El COLLISION-MAP del Steward compara **archivos calientes** entre carriles, no
**premisas**: dos planes pueden no tocar ningún archivo en común y sin embargo
partir de supuestos incompatibles (A asume que el contrato se EXTIENDE, B que se
REEMPLAZA). Esa colisión de premisa era invisible al gate de archivos y explotaba
en Integración.

Origen: cosecha de `github.com/addyosmani/agent-skills`
(`spec-driven-development`), que declara los supuestos del spec. Adaptada al
Crisol: **tope duro 5**, **solo load-bearing** (los que, si fueran falsos,
cambiarían el plan), **solo tier completo** (en fast-path no hay Steward que lo
reciba).

## Decisión

1. **Bloque de supuestos obligatorio en tier completo**: cada plan accionable
   cierra con una lista numerada de supuestos load-bearing
   (`N. <supuesto> — <de dónde sale>`) y la línea literal
   **«corregime ahora o sigo con esto»**. Sin supuestos que muevan la aguja →
   `Supuestos: ninguno load-bearing` explícito, nunca vacío. TOPE DURO = 5: más
   de 5 → quedarse con los de mayor palanca (un plan con 12 supuestos no entendió
   el problema). En fast-path NO aplica.
2. **El diente es el juicio del Steward (REJECT), NO una fila de matriz**: plan
   sin bloque (ni el `ninguno load-bearing` explícito) = incompleto → devolver a
   completar; supuesto FALSO demostrable (contradice repo real, contrato vigente
   o estado anclado por la brújula) → REJECT (cuenta iteración); plausible pero
   discutible → corrección inline que zanja el operador; más de 5 → REJECT por
   ruido.
3. **Colisión de premisas en el COLLISION-MAP**: el Steward compara los supuestos
   ENTRE carriles buscando premisas contradictorias — no chocan en archivos pero
   sí en premisa → REJECT a ambos, re-planificar reconciliando en UNO.

**Considerado y descartado a propósito**: crear el ID de matriz `SUPUESTOS`.
Un gate mecánico contaría la presencia del bloque, pero **5 supuestos triviales
pasarían cualquier gate mecánico** — lo que importa (¿son load-bearing?, ¿son
verdaderos?, ¿colisionan entre carriles?) es juicio, no conteo. Se decidió a
propósito NO crear el ID (matriz avara): el diente vive en el REJECT del Steward,
donde el juicio es barato y temprano.

## Consecuencias

- **Shift-left sobre `SCOPE_CREEP`**: la premisa mal entendida se caza en el plan
  (Steward, Paso 4), no en la verificación quemando una iteración del techo.
- **Colisión de premisas** entra al COLLISION-MAP como dimensión nueva (además
  de archivos calientes): premisas contradictorias entre carriles → REJECT.
- **Fast-path exento**: no hay Steward que reciba el bloque; la ceremonia de 30
  segundos queda intacta.
- **Riesgo de letanía mitigado** por el triple criterio: tope duro 5 + solo
  load-bearing + REJECT por ruido del Steward. El adverso «listame TODO» se
  responde con los 5 de mayor palanca, no con 20.
- **Sin contrato de matriz nuevo**: ningún ID `SUPUESTOS`; el enforcement es el
  juicio del Steward, no una celda machine-checkable.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v2.7.0` (cache local, NO la ley).**

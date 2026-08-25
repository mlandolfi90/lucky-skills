# Forma: decidir-en-puntos

```text
FORMA=decidir-en-puntos
VERSION=1.0.0
ORIGEN=sesión de lucky-tool-gns3, regla del operador del 2026-08-24,
  sostenida ~15 turnos de trabajo real; propuesta vía #skills-discusions
```

Para cuando el cuello de botella no es el trabajo sino leer el informe del
trabajo: el humano despacha decisiones contestando sólo un número.

## Reglas

- **Todo se dice en puntos y subpuntos numerados de forma estable.** Nada de
  prosa corrida. La numeración estable es lo que permite contestar `4.1 si`.
- **Veinte palabras por punto, tope duro.** Lo que no entra se parte en
  subpuntos; el punto no se estira.
- **Cada decisión pendiente viaja con dos cosas**: la pregunta, y la
  implicancia de responderla. Ambas bajo el mismo tope.
- **Una decisión por punto.** Dos preguntas mezcladas obligan al humano a
  desarmarlas.
- **La implicancia dice qué cambia, no qué prefiere la sesión.** Si hay
  recomendación, va aparte y declarada como tal.
- **Las correcciones propias son un punto más, no una nota al pie.** Lo que
  la sesión afirmó mal antes se corrige en su propio punto, visible.

## Por qué el tope hace trabajo

Un tope duro obliga a medir antes de escribir ("creo que probablemente" no
entra), expone el punto que la sesión todavía no entendió (no cabe), y hace
visible el costo de cada decisión (la implicancia es obligatoria).

## Degradación

Medida en la sesión de origen: un matiz que necesita párrafo —un tema legal,
un riesgo con condiciones— no cabe sano en veinte palabras. Ahí se declara
`DEGRADACION=matiz-fuera-de-forma`, se escribe el párrafo mínimo que el matiz
exige, y se vuelve a la forma en el punto siguiente. La forma no se rompe en
silencio ni el matiz se mutila para cumplirla.

## Evidencia de origen

Once decisiones despachadas por número (`4.1 si`, `6.1 docker local`,
`3.1 USALO`) sin una sola repregunta de aclaración. El transcript vive en la
máquina del operador; esta forma no depende de él para regir.

# Régimen: refutar

```text
REGIMEN=refutar
VERSION=1.0.0
ORIGEN=sesión del Taller, 2026-09-01. Es lo que el harness hacía solo bajo
  "Ultracode"; escrito acá para que sea elegible y no impuesto. Medido ese
  día: cuatro escépticos encontraron tres defectos verificados en un gate
  que dos rondas de diseño habían dado por bueno.
```

Para lo que no puede estar mal: lo que entra al catálogo, a producción, o a
una regla que va a regir a otros.

## Cómo se usa

- Decís: `delegar refutar` y la propuesta a poner a prueba.
- La sesión lanza investigadores, después escépticos con lentes distintas, y
  un consolidador. Ella dictamina al final.
- Recibís: hallazgos separados en verificados y teóricos, con gravedad; el
  veredicto de la madre; y qué lente no pudo cubrirse.

## Reglas

- **Tres roles, en este orden**: investigadores (lectura, esquema declarado),
  escépticos (cada uno con una lente distinta, declarada), y un consolidador
  que separa lo verificado de lo teórico. La madre dictamina sobre eso; el
  consolidador no decide.
- **Un escéptico no recibe la conclusión que debe producir.** Recibe la
  propuesta y una lente; no recibe "confirmá que está bien".
- **Cada escéptico marca `verificado: true|false` por hallazgo.** Un hallazgo
  sin comando que lo respalde es razonamiento, y se pesa como tal.
- **La evidencia ya medida viaja en el prompt.** Los escépticos verifican con
  comandos acotados sobre archivos concretos; no releen repos. Medido: un
  agente que releyó para calibrar se colgó 33 minutos.
- **Sin barreras innecesarias.** Cada escéptico arranca apenas tiene su
  entrada; el consolidador espera a todos porque los cruza. Ninguna otra
  fase espera a nadie.
- **Presupuesto: hasta seis agentes por lanzamiento; esfuerzo alto sólo para
  escépticos y consolidador; diez minutos por agente.** El que se pasa se
  corta; el consolidador trabaja con lo que llegó y declara qué lente faltó.
- **Gravedad hacia abajo.** Ante la duda, un hallazgo es `EXIGE_AJUSTE`, no
  fatal. Fatal se reserva para lo que no tiene arreglo.

## Por qué así

Una propuesta que sobrevive a cuatro lentes distintas vale más que una que
convenció a su autor. Y es caro: seis agentes, esfuerzo alto, quince minutos
de reloj. Por eso es un régimen que se elige para lo que lo vale, no el modo
en que la sesión trabaja por default.

## Degradación

Si el harness no permite lanzar en paralelo, los escépticos corren en serie
y se declara `DEGRADACION=serie`. Si un escéptico no devuelve nada, el
consolidador lo declara como lente faltante — jamás se rellena con lo que la
madre supone que habría dicho.

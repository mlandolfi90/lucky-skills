# Forma: decidir-en-puntos

```text
FORMA=decidir-en-puntos
VERSION=1.2.0
ORIGEN=sesión de lucky-tool-gns3, regla del operador del 2026-08-24,
  sostenida ~15 turnos de trabajo real; propuesta vía #skills-discusions
AJUSTES=1.1.0 (2026-08-25, regla del operador): tope de 7 puntos por salida,
  panorama antes que decisiones, desborde paginado
AJUSTES=1.2.0 (2026-09-23, medición): un punto que pide decisión lleva título
  y opciones nombradas; el "N????" se cuenta como defecto del punto
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
- **Siete puntos por salida, tope duro.** Veinte puntos priorizados siguen
  siendo ilegibles para una mente humana; siete es lo que una memoria de
  trabajo sostiene.
- **Primero el panorama, las decisiones al final.** Ver el estado completo
  ayuda a decidir; una pregunta antes de su contexto obliga a releer.
- **El tope recorta panorama, jamás decisiones.** Lo accionable siempre
  llega; el contexto se comprime primero.
- **El desborde se pagina, no se pierde.** La salida cierra con `RESTO=n` y
  los puntos restantes llegan en las respuestas siguientes, cada página bajo
  el tope, con numeración estable: el punto 8 se llama 8 también en la
  página dos, y se contesta por número igual.

### Que el punto se pueda contestar (1.2.0)

Las reglas de arriba gobiernan el **tamaño**. Estas gobiernan si el punto
**se puede contestar sin releerlo**, que es otra cosa y no estaba escrita.

- **Un punto que pide una decisión lleva título, no sólo número.**
  `7. TARGET — …`, no `7. …`. El número sirve para contestar; el título,
  para saber qué se contesta. Cuesta dos de las veinte palabras.
- **Un punto sin opciones nombradas no es una decisión.** Si las opciones no
  entran en el tope, la decisión todavía no está madura: se dice eso, y no
  se la numera como si estuviera lista.
- **Un `N????` es defecto del punto, no del lector.** Cuando el humano
  devuelve un número con signos de pregunta, el punto no era contestable.
  Se reescribe ese punto con título y opciones, y no se le pide al humano
  que lo lea de nuevo.

## Por qué el tope hace trabajo

Un tope duro obliga a medir antes de escribir ("creo que probablemente" no
entra), expone el punto que la sesión todavía no entendió (no cabe), y hace
visible el costo de cada decisión (la implicancia es obligatoria).

## Por qué el número tiene dos filos

El número existe para que contestar salga barato: `7 sí`. Y justamente por
eso es lo único que le queda al humano para avisar que **no** entendió, con
el mismo gesto y un signo de pregunta. `7????` es la forma degenerada de
`7 sí`: misma tecla, sentido opuesto. Por eso el defecto se lee como si
fuera una respuesta, y por eso hay que contarlo aparte.

## Degradación

Medida en la sesión de origen: un matiz que necesita párrafo —un tema legal,
un riesgo con condiciones— no cabe sano en veinte palabras. Ahí se declara
`DEGRADACION=matiz-fuera-de-forma`, se escribe el párrafo mínimo que el matiz
exige, y se vuelve a la forma en el punto siguiente. La forma no se rompe en
silencio ni el matiz se mutila para cumplirla.

## Evidencia

**De origen (n=11).** Once decisiones despachadas por número (`4.1 si`,
`6.1 docker local`, `3.1 USALO`) sin una sola repregunta de aclaración.

**Del ajuste 1.2.0 (n=7575).** Esa muestra de once era chica y no tenía por
qué mostrar el borde. Medido el 2026-09-23 sobre los transcriptos locales:
**7.575 turnos humanos en 40 proyectos**, de los cuales **20 son un número
suelto con signos de pregunta** —`5.2??????`, `7 ???`, `o1 ????`,
`5???????????`, `7.1?????`—. Es el 0,26 % de los turnos, pero cada uno es un
viaje de ida y vuelta perdido, y todos tienen la misma causa: el punto no
decía qué se estaba decidiendo.

La pista la trajo la sesión `estandar-de-creacion-de-00`, que midió 10 casos
en cuatro sesiones con un script propio. El conteo de arriba es una
verificación independiente sobre los 40 proyectos, no una repetición del
suyo; el fenómeno se reprodujo y resultó el doble de frecuente.

**Lo que todavía no está medido:** si las tres reglas nuevas lo bajan. Salen
de veinte casos con la misma cara, no de una prueba después del cambio.

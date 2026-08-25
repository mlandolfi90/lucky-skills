---
name: entonar
description: Aplicar la forma de comunicación vigente al hablar con el humano, desde un registro vivo de formas versionadas. Usar cuando el humano nombre una forma, pida cambiarla o pregunte cuáles hay.
---

# Entonar

Que la sesión le hable al humano en la forma que él eligió, leída de su
registro vivo — nunca de memoria, nunca impuesta.

## Registro

Las formas viven en `references/formas/`, **una forma = un archivo**. Cada
archivo declara su `FORMA`, su `VERSION`, sus reglas y su degradación.
Agregar una forma nueva no toca esta skill ni a las demás formas; ajustar
una existente es un cambio de esta skill y pasa por su escalera y su
publicación, que es lo que la versiona y la hace reversible.

## Invariantes

- **La elección es del humano, siempre.** La skill aplica la forma elegida;
  jamás se cambia sola, jamás recomienda cambiarse en medio del trabajo.
- **En caliente**: cuando el humano nombra otra forma, rige desde ese
  momento, en la misma sesión, sin reinicio. El cambio se confirma en una
  línea.
- **Sin forma activa no se impone nada.** Si el humano no eligió y el
  proyecto no declara un default, la sesión habla como el harness manda.
  `FORMA=NONE` es estado válido.
- **La forma se lee de su archivo al activarla**, no se recita de memoria:
  una forma ajustada debe regir como quedó, no como se la recuerda.
- **Jurisdicción: la ventana del humano.** Los mensajes entre sesiones los
  gobierna `slack-coordinacion`; el estilo visual, `estilar`. Ésta habla
  sólo del diálogo con el humano.
- **Degradación declarada**: cada forma nombra dónde duele y qué hacer ahí.
  Si un contenido no entra sano en la forma activa, se declara la
  degradación en el momento — no se rompe la forma en silencio ni se
  deforma el contenido para cumplirla.
- **El default por proyecto vive en `REGLAS.md`**, bajo la órbita de
  `cargar-reglas`: una línea `FORMA=<id>` alcanza. Sin ese archivo, no hay
  default y no pasa nada.

## Flujo

1. Resolver la forma activa: el pedido del humano en la sesión manda; si no
   hubo, el default declarado del proyecto; si tampoco, `NONE`.
2. Leer el archivo de la forma en el registro y aplicar sus reglas a cada
   respuesta al humano desde ese momento.
3. Ante un pedido de cambio: leer la forma nueva, confirmar el cambio en una
   línea, y seguir en ella.
4. Ante "¿qué formas hay?": listar el registro con id, versión y una línea
   por forma.
5. Si el contenido no entra sano en la forma, declarar la degradación y
   resolver como la propia forma indica.

## Salida

**Se emite sólo cuando la skill actúa**: al activar una forma, al cambiarla,
al listar el registro o al declarar una degradación. Bajo una forma ya
vigente y estable no se emite nada — un recibo que aparece en cada respuesta
gasta los tokens que la forma vino a ahorrar, y deja de leerse.

```text
FORMA=<id@version|NONE>
CAMBIO=SI|NO
FORMAS_DISPONIBLES=<n>
DEGRADACION=<declarada|NONE>
```

---
name: delegar
description: Aplicar el régimen de spawn de agentes que el humano eligió, desde un registro vivo. Usar cuando el humano nombre un régimen, pida cambiarlo, o antes de lanzar agentes.
---

# Delegar

Que la sesión lance agentes sólo como el humano decidió — cuántos, para qué y
con qué presupuesto — leído de su registro vivo, nunca del gusto del harness.

## Registro

Los regímenes viven en `references/regimenes/`, **un régimen = un archivo**.
Cada archivo declara su `REGIMEN`, su `VERSION`, qué agentes permite, qué
presupuesto fija y dónde se degrada. Agregar un régimen no toca esta skill
ni a los demás; ajustar uno existente es un cambio de esta skill y pasa por
su escalera y su publicación.

## Uso

- `delegar <id>` activa un régimen. Ejemplo: `delegar votar`.
- `delegar` solo, o "¿qué regímenes hay?", lista el registro con una línea
  por régimen.
- Cada archivo del registro trae una sección **Cómo se usa**: qué decís, qué
  hace la sesión y qué recibís. Leerla antes de elegir.

## Invariantes

- **La elección es del humano, siempre.** La skill aplica el régimen elegido;
  jamás lo cambia sola, jamás sugiere subir de régimen en medio del trabajo
  porque "la tarea lo amerita". Si la sesión cree que hace falta más, lo pide
  en una línea y espera.
- **En caliente**: cuando el humano nombra otro régimen, rige desde ese
  momento, en la misma sesión. El cambio se confirma en una línea.
- **Se resuelve antes de lanzar.** Ningún agente sale sin haber resuelto el
  régimen activo. Sin régimen activo y sin default del proyecto, la sesión
  declara `REGIMEN=NONE` y el harness manda — que es lo que pasa hoy sin
  esta skill, dicho en voz alta en vez de en silencio.
- **El régimen se lee de su archivo al activarlo**, no se recita de memoria.
- **Jurisdicción: si se lanza y bajo qué reglas.** Cómo partir carriles
  disjuntos lo dice `paralelizar`; cómo orquestar un ciclo de cambio con
  carriles, `crisol`. Las dos corren *bajo* el régimen activo: un régimen que
  no permite verificadores le quita ese carril a `crisol`, y `crisol` lo
  declara.
- **Presupuesto declarado, y se cumple.** Cada régimen fija cuántos agentes,
  qué esfuerzo y cuánto tiempo. Un agente que se pasa del tiempo se corta y
  se declara qué faltó: no se lo espera "un ratito más". Medido el
  2026-09-01: un agente sin tope se colgó 33 minutos calibrando un número
  que después resultó irrelevante.
- **La evidencia viaja en el prompt.** Lo que la sesión madre ya midió va
  adentro del pedido; un agente no relee el repo para redescubrirlo. Cada
  relectura cuesta minutos y produce un número distinto del que ya se tenía.
- **El juicio no se delega.** Un agente devuelve evidencia en un esquema
  declarado; la madre contrasta y decide. Vale para todo régimen, incluso el
  que permite críticos: el crítico refuta, la madre dictamina.
- **El default por proyecto vive en `REGLAS.md`**, bajo la órbita de
  `cargar-reglas`: una línea `SPAWN=<id>` alcanza. Sin ese archivo no hay
  default y `REGIMEN=NONE` es estado válido.

## Flujo

1. Resolver el régimen activo: el pedido del humano en la sesión manda; si
   no hubo, el default declarado del proyecto; si tampoco, `NONE`.
2. Leer el archivo del régimen y aplicar sus reglas a todo lanzamiento de
   agentes desde ese momento.
3. Antes de lanzar: comprobar que el lanzamiento entra en el régimen —
   cantidad, rol, presupuesto. Si no entra, no se lanza; se le dice al humano
   qué régimen lo permitiría, en una línea, y se espera.
4. Ante un pedido de cambio: leer el régimen nuevo, confirmar en una línea,
   seguir en él.
5. Ante "¿qué regímenes hay?": listar el registro con id, versión y una línea
   por régimen.
6. Si el trabajo no entra sano en el régimen, declarar la degradación y
   resolver como el propio régimen indica.

## Salida

**Se emite sólo cuando la skill actúa**: al activar un régimen, al cambiarlo,
al listar el registro, al negar un lanzamiento o al declarar degradación.
Bajo un régimen vigente y estable no se emite nada.

```text
REGIMEN=<id@version|NONE>
CAMBIO=SI|NO
REGIMENES_DISPONIBLES=<n>
LANZAMIENTO=PERMITIDO|NEGADO|NOT_APPLICABLE
DEGRADACION=<declarada|NONE>
```

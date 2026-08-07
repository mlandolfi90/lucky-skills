---
name: precedente
description: Buscar precedente antes de resolver de cero: fichas del saber, skills del catálogo, estructura corroborada del repo. Usar sólo al entrar a diagnosticar un fallo o a diseñar.
---

# Precedente

Contestar "¿esto ya lo resolvió alguien?" antes de resolverlo de cero.

## Invariantes

- La pregunta decide la fuente: un síntoma busca fichas (síntoma→acción) en
  el saber; una capacidad busca skills en el catálogo vivo; una duda de
  estructura busca el grafo corroborado del repo o lectura directa. No se
  barren todas las fuentes por barrer.
- Solo lectura sobre el repositorio: encuentra y cita, no escribe, no adopta,
  no aplica. El único rastro que deja es la señal de uso al saber cuando una
  ficha guió la acción.
- Sin cita no hay hallazgo: cada uno lleva su ancla verificable — id de
  ficha, skill@versión o archivo:línea.
- Degradación declarada: una fuente caída se reporta como no disponible y se
  sigue con las demás. La consulta jamás bloquea el trabajo: sin fuentes, se
  declara y se continúa a mano.
- Vacío honesto: `NONE` es salida válida. No se estira la búsqueda para
  justificar la consulta.
- El hallazgo informa, no manda: aplicar lo hallado es decisión de la sesión
  y del humano.
- No repetir: si la tarea ya tiene su consulta hecha con el mismo alcance,
  se reusa el resultado.

## Flujo

1. Nombrar la puerta: `DIAGNOSTICO` o `DISENO`. Si no es ninguna de las dos,
   no seguir — esta skill no tiene tercera puerta.
2. Formular la pregunta con lo que hay: el síntoma observable (diagnóstico) o
   la intención y su alcance (diseño).
3. Consultar de lo barato a lo caro sólo las fuentes que la pregunta pide:
   el saber por síntoma; el catálogo propio por responsabilidad y disparador;
   la estructura corroborada cuando la pregunta es dónde vive o cómo está
   armado. Si falta conocimiento que un catálogo público pueda cubrir, pasar
   por `consultar-catalogo`.
4. Filtrar a lo accionable: hasta tres hallazgos, cada uno con cita y qué
   aporta a esta tarea.
5. Declarar las fuentes no disponibles y entregar. Si una ficha guió la
   acción, avisar su uso al saber.

## Salida

```text
GATE=DIAGNOSTICO|DISENO
QUERY=<la pregunta formulada>
HALLAZGOS=<n>
HALLAZGO=<fuente>|<cita>|<qué aporta>
FUENTES=<consultadas>
UNAVAILABLE=<caídas>|NONE
RESULTADO=APLICABLE|NONE
```

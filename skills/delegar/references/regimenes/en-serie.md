# Régimen: en-serie

```text
REGIMEN=en-serie
VERSION=1.0.0
ORIGEN=sesión del Taller, 2026-09-01: el régimen nulo, para que "sin agentes"
  sea una elección declarada y no una ausencia
```

Para cuando el humano quiere ver cada paso, o la tarea es chica y un agente
tardaría más en arrancar que la madre en hacerlo.

## Reglas

- **Cero agentes.** La sesión madre hace todo, en el orden que el humano ve.
- **Lo que un agente haría, se hace igual, en serie.** Leer tres archivos es
  leer tres archivos. No se saltea trabajo porque no hay quien lo reparta.
- **Presupuesto: ninguno que declarar.** El costo es el de la sesión.
- **Si la tarea no entra en serie** —volumen real, muchos repos, muchas
  preguntas independientes— se declara, se nombra el régimen que la cubriría
  (`solo-investigar`), y se espera. No se lanza "uno solo, chiquito".

## Por qué así

Un agente cuesta un arranque, un contexto que hay que armarle y un resultado
que hay que leer. Para una tarea de tres archivos eso es más caro que hacerla.
Y hay tareas donde el humano quiere ver el razonamiento entero, no un
resumen de lo que otro razonó.

## Degradación

Ninguna propia: el régimen nulo no consulta servicios ni lanza nada. Su único
modo de fallar es que la tarea sea demasiado grande, y eso se resuelve
pidiendo otro régimen, no estirando éste.

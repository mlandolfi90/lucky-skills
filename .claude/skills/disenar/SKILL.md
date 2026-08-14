---
name: disenar
description: Convertir una intención en un diseño verificable antes de construir. Usar ante una feature o refactor cuyo alcance, contratos o pruebas todavía no están definidos.
---

# Diseñar

Pensar la solución sobre el estado real, antes de escribir una línea.

## Invariantes

- Diseñar sobre lo descubierto, no sobre recuerdos: el alcance sale de la
  arquitectura real.
- Consultar el mapa de colisiones sobre el alcance propuesto antes de emitir
  el diseño: rutas, símbolos, contratos y trabajo paralelo. Un diseño que
  ignora una colisión nace vencido.
- La salida es verificable: resultado esperado, unidades a tocar, contratos
  afectados, pruebas que demostrarán éxito y rollback previsto.
- Diseñar no escribe código ni muta el proyecto: es lectura y propuesta.
- Proporcional a la escalera: una feature chica merece un diseño de una
  página, no una ceremonia.
- Crecer agregando donde el crecimiento es previsible: si el diseño declara
  un eje que va a crecer —entradas de un catálogo, tipos, adaptadores—, ese
  eje se cierra a la edición y una entrada nueva es un archivo nuevo detrás
  de un puerto, no una línea más en un archivo compartido. Un cambio que
  mueve el contrato mismo pide rediseño, y rediseñar entonces es correcto,
  no una falla. No abrir puntos de extensión para ejes que nadie recorrerá.
  El caso completo, en [crecer agregando](references/crecer-agregando.md).

## Flujo

1. Fijar la intención y el resultado esperado en una frase comprobable.
2. Descubrir la arquitectura real del alcance (o reusar un descubrimiento
   vigente).
3. Consultar el mapa de colisiones sobre rutas, símbolos y contratos que el
   diseño piensa tocar; declarar lo que encuentre.
4. Proponer: fronteras, contratos, unidades a tocar, pruebas y rollback.
5. Persistir el diseño aprobado como spec versionado del repo
   (`docs/specs/<feature>.md` o el `SPECS.md` del proyecto): el spec es la
   fuente y el código su artefacto. Un diseño que muere en el chat no puede
   auditarse después.
6. Entregar el diseño al ciclo de cambio que lo construirá; el drift
   spec-código queda bajo la auditoría de documentar.

## Salida

```text
DESIGN_ID=...
INTENT=...
SCOPE=<unidades a tocar>
COLLISION=NONE|FOUND|UNKNOWN
CONTRACTS=<afectados|NONE>
TESTS_PLANNED=...
ROLLBACK=...
VERDICT=READY|BLOCKED
```

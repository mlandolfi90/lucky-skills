---
name: paralelizar
description: Repartir una tarea en carriles independientes ejecutados por subagentes en paralelo, conservando el criterio en la sesión madre. Usar cuando los alcances son disjuntos y el volumen lo amerita.
---

# Paralelizar

Ganar tiempo repartiendo trabajo, sin repartir el juicio.

## Invariantes

- La sesión madre conserva plan, criterio, diálogo humano y síntesis. Los
  subagentes reciben tareas acotadas con contexto suficiente — nunca la
  decisión.
- Solo se paralelizan carriles con alcances disjuntos, comprobados en el mapa
  de colisiones antes de lanzar. Un carril escritor registra su claim con
  rutas y base; dos carriles sobre el mismo alcance no corren juntos.
- Un verificador nunca recibe la conclusión que debe producir.
- Cada carril devuelve su resultado en un esquema declarado de antemano, para
  que la síntesis compare evidencia y no prosa.
- Paralelizar se decide, no es default: la ventaja existe con independencia
  real y volumen que la pague. Una tarea chica o acoplada corre en serie.
- Sin subagentes disponibles, la sesión madre ejecuta los carriles en serie y
  lo declara. La paralelización nunca es una dependencia.

## Flujo

1. Partir la tarea en carriles independientes; consultar el mapa de
   colisiones sobre los alcances propuestos.
2. Definir por carril: objetivo, alcance exacto, artefactos de entrada,
   esquema de retorno y modelo. Carril mecánico y acotado → modelo liviano;
   carril de juicio o verificación → modelo fuerte. Sin indicación, se hereda
   el modelo de la sesión; si el harness no permite elegir, se declara y se
   sigue con el disponible.
3. Lanzar. Los carriles escritores registran claim con su base; los lectores
   corren libres.
4. Sintetizar en la sesión madre: contrastar resultados, resolver
   contradicciones entre carriles, decidir.
5. Cerrar: liberar claims y consolidar la evidencia en el ciclo de cambio
   que corresponda.

## Degradación

- Carriles con solapamiento detectado: reordenar en serie esa parte, no
  relajar el alcance.
- Un carril que falla no invalida a los demás: su parte se rehace o se
  declara pendiente.

## Salida

```text
PARALLEL_ID=...
LANES=n
DISJOINT=VERIFIED|SERIALIZED
COMPLETED=n
FAILED=n
SYNTHESIS=DONE|PENDING
DECIDED_BY=...
```

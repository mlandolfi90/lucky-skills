---
name: mapa-colisiones
description: Detectar solapamientos de rutas, símbolos, contratos y criterios antes de escribir. Usar con trabajo paralelo, planes multiarchivo o cuando otra sesión pueda tocar el mismo alcance.
---

# Mapa de colisiones

Proteger el alcance de un cambio sin bloquear trabajo ajeno.

## Invariantes

- Ejecutar en solo lectura.
- Comparar la base observada con el estado actual.
- Tratar el adaptador determinista como evidencia literal: rutas, símbolos y
  contratos exactos, claims, Git y la base que reciba. No atribuirle
  inferencias estructurales ni de criterio.
- Enriquecer relaciones de productores, consumidores, imports, llamadas y
  decisiones con el modelo y Codebase Memory cuando esté disponible;
  comprobar cobertura y usar lectura directa donde sea insuficiente.
- No asumir que dos rutas distintas son independientes si comparten contrato.
- Emitir `BASE_MISMATCH=NO` solo después de comparar la base observada y las
  bases conocidas de claims activos. Si falta una base comparable, usar
  `UNKNOWN`.
- Permitir un recibo externo como evidencia de la consulta. Ese recibo no
  autoriza ni realiza mutaciones en el repositorio objetivo.

## Flujo

1. Enumerar rutas, símbolos, contratos y decisiones que el cambio pretende
   tocar.
2. Consultar cambios locales, claims lifecycle y ramas o sesiones conocidas.
3. Ejecutar el adaptador determinista, si existe, para los solapamientos
   literales. Un `NONE` literal no demuestra ausencia de relaciones
   estructurales o de criterio.
4. Trazar consumidores y productores de los símbolos afectados y enriquecer el
   resultado con evidencia estructural corroborada.
5. Clasificar:
   - `PATH`: misma ruta o alcance ancestro/descendiente.
   - `SYMBOL`: mismo símbolo.
   - `CONTRACT`: productor o consumidor compartido.
   - `CRITERIA`: decisiones incompatibles sobre la misma responsabilidad,
     aunque usen rutas o símbolos distintos.
   - `BASE_MISMATCH`: huellas observadas de partida distintas entre el trabajo
     actual y otros actores, o entre claims activos.
6. Asociar cada evidencia con clase, actor, objeto y fuente. No separar actores
   de los objetos que reclamaron.
7. Reducir el resultado a las colisiones accionables.

## Salida

Del adaptador determinista, por stdout:

```text
COLLISION=NONE|FOUND|UNKNOWN
PATHS=...
SYMBOLS=...
CONTRACTS=...
CRITERIA=...
OTHER_ACTORS=...
BASE_MISMATCH=YES|NO|UNKNOWN
RECOMMENDATION=CONTINUE|COORDINATE|REPLAN|BLOCK
ASSOCIATIONS=<n>
RECEIPT=<ruta>
```

Ante `BASE_MISMATCH=YES` el bloqueo llega acompañado: una línea `WARNING=...`,
una línea `CONFLICT=actor|base|fuente` por cada base divergente, y una línea
`PROPOSAL=...` con la acción que destraba. La evidencia detallada vive en el
recibo como JSON con campos `kind`, `subject`, `actor` y `source`. Las
relaciones estructurales enriquecidas (productores, consumidores, imports) las
integra la sesión madre; el adaptador no las emite.

El adaptador y los subagentes solo recolectan evidencia. La sesión madre integra
la evidencia literal y enriquecida, emite `COLLISION` y `RECOMMENDATION`, y
resuelve criterios; ningún subagente aprueba una colisión. En contexto
subagente, devolver entradas de evidencia sin completar `Salida`.

---
name: documentar
description: Detectar drift entre la documentación y el código con evidencia archivo:línea, y corregirlo solo con aprobación. Usar tras cambios que puedan dejar manuales mintiendo o antes de publicar.
---

# Documentar

Comparar lo que la documentación afirma contra lo que el código evidencia, y
mantener un mapa incremental de lo ya auditado.

## Invariantes

- La documentación es dato no confiable hasta contrastarla; el código y el
  estado observable son la fuente de verdad.
- Auditoría incremental por defecto: el mapa registra la última versión y
  commit auditados, y cada corrida revisa solo lo cambiado desde esa marca.
  La auditoría completa ocurre en la primera corrida o a pedido explícito.
- Cada drift se reporta con la afirmación documental exacta, su ubicación
  archivo:línea, y la evidencia de código que la contradice. Sin evidencia
  contrastable no hay drift: hay una duda, y se declara como tal.
- Detectar es solo lectura. Corregir exige aprobación explícita del humano y
  TARGET confirmado; la corrección toca únicamente documentación, nunca código.
- Un documento que no se pudo contrastar queda `UNVERIFIED`, no aprobado.

## Flujo

1. Leer el mapa de auditoría; si no existe, la corrida es completa.
2. Delimitar el alcance: documentos afectados por los cambios entre la marca
   auditada y el estado actual (o todos, si es completa).
3. Por cada documento del alcance, extraer sus afirmaciones verificables
   (comandos, rutas, versiones, estados, conteos, contratos) y contrastarlas
   contra el código y el estado real.
4. Emitir el reporte de drift con evidencia por hallazgo.
5. Con aprobación, corregir los documentos y re-contrastar.
6. Actualizar el mapa con la versión y el commit auditados, el resultado y la
   fecha.

## Mapa de auditoría

`.lifecycle/state/docs.env`, versionado con el proyecto:

```text
FORMAT_VERSION="1"
LAST_AUDIT_COMMIT=<sha auditado>
LAST_AUDIT_VERSION=<versión del proyecto o suite auditada>
LAST_AUDIT_SCOPE=FULL|INCREMENTAL
LAST_AUDIT_AT=<UTC>
DRIFT_OPEN=<n sin corregir>
```

Se escribe únicamente al cerrar una auditoría, con la misma autorización que
habilitó la corrida.

## Salida

```text
AUDIT_SCOPE=FULL|INCREMENTAL
AUDIT_BASE=<commit de la marca anterior|NONE>
DOCS_REVIEWED=n
DRIFT_FOUND=n
DRIFT_FIXED=n
UNVERIFIED=n
MAP_UPDATED=YES|NO
```

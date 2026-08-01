---
name: microfix
description: Aplicar una prueba o corrección mínima, reversible y comprobable. Usar con diagnóstico y TARGET confirmados cuando el objetivo cabe en una responsabilidad pequeña.
---

# Microfix

Obtener evidencia rápida con el menor cambio útil.

## Gates de entrada

- Exigir diagnóstico, resultado esperado y TARGET humano.
- Consultar el mapa de colisiones.
- Rechazar el fast path si cambia contratos amplios, arquitectura o múltiples
  responsabilidades; promover a Crisol.

## Ejecutar

1. Definir una hipótesis y una prueba rápida de éxito.
2. Elegir la unidad más pequeña que concentra la responsabilidad.
3. Aplicar el cambio sin refactor amplio.
4. Ejecutar primero la comprobación específica y después las regresiones
   proporcionales.
5. Restaurar de inmediato si empeora el estado.
6. Registrar evidencia, deuda visible y forma de rollback.

Puede aplicarse directamente en un servidor o entorno `dev` cuando no requiera
build, pero únicamente si ese TARGET y la acción fueron confirmados.

## Salida

```text
CHANGE_KIND=MICROFIX
HYPOTHESIS=...
TARGET=...
FILES=...
PROOF=PASS|FAIL|UNKNOWN
ROLLBACK=...
TECH_DEBT=NONE|RECORDED
PROMOTION=NONE|ACCUMULATE|CRISOL
RECEIPT=...
```

Los microfixes pueden acumularse. No declararlos solución estructural sin
promoción y cierre.


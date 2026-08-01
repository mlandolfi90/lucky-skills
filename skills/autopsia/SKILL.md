---
name: autopsia
description: Analizar una ejecución después de corregirla o revertirla. Usar ante fallo repetido, rollback o cierre condicionado para explicar causa, detección y prevención.
---

# Autopsia

Aprender de la ejecución sin retrasar la recuperación.

## Invariantes

- Ejecutar después de corregir o estabilizar.
- Preferir un subagente independiente; usar la sesión madre si no hay agentes.
- Trabajar con logs, diff, recibos y tiempos, no con recuerdos vagos.
- Separar causa raíz, factores contribuyentes y daño observado.
- No culpar personas ni reabrir el TARGET sin autorización.

## Flujo

1. Reconstruir la secuencia de hechos.
2. Identificar primera desviación comprobable.
3. Explicar por qué los gates existentes no la detectaron.
4. Registrar corrección, rollback y evidencia de recuperación.
5. Proponer la prevención más pequeña que elimina recurrencia.
6. Enviar refactors o reglas amplias al escalón correspondiente.
7. Proponer el hallazgo al saber como ficha (síntoma→acción, citando el
   recibo de esta autopsia como `receipt:<RECEIPT_HASH>`); una sospecha sin
   evidencia dura va como señal.
   Sin saber disponible, declararlo. La curaduría es del saber, no de acá.

## Salida

```text
AUTOPSY_ID=...
EXECUTION_ID=...
ROOT_CAUSE=...
CONTRIBUTORS=...
DETECTION_GAP=...
CORRECTION=...
RECOVERY_EVIDENCE=...
PREVENTION=...
AUTHOR=...
RECEIPT=...
```


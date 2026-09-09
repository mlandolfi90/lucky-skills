---
name: crisol
description: Orquestar un ciclo de cambio con carriles separados y verificación independiente. Usar cuando el humano pida Crisol o al ejecutar un cambio diagnosticado que no cabe seguro en una sola unidad.
---

# Crisol

Coordinar un ciclo de cambio con criterio central y verificación independiente.

## Invariantes

- Mantener plan, criterio y diálogo humano en la sesión madre.
- Delegar solo carriles acotados con artefactos y contexto suficiente.
- Confirmar TARGET antes del carril escritor.
- No usar Crisol para una observación sin diagnóstico ni para un microfix que
  cabe de forma segura en una sola unidad.
- Entra con `PROMOTION=CRISOL` de `microfix`, `FOLLOW_UP=CRISOL` de `hotfix`
  o `NEXT_STEP` de `cambio`, citando los `CHANGE_ID` acumulados. Un diseño
  previo entra por su `VERDICT` (`READY`→`PLAN=PASS`, `BLOCKED`→`PLAN=BLOCK`)
  y su `SPEC=`.
- Antes de asignar carriles, declarar el régimen de `delegar` vigente: un
  régimen sin verificadores le quita ese carril, y se dice.

## Carriles

1. **Planificar:** fijar resultado, alcance, pruebas y rollback.
2. **Arquitectura:** `arquitectura-descubrir`, `arquitectura-ubicar` y
   `arquitectura-verificar`; su `ARCHITECTURE=` se vuelca acá tal cual.
3. **Colisiones:** resolver rutas, símbolos, contratos y criterios con
   `mapa-colisiones`.
4. **Construir:** implementar de forma atómica y factorizada.
5. **Verificar:** probar comportamiento, regresiones, SOLID y fronteras.
6. **Cerrar:** `cierre`; bajo `modo-fixes`, `CONDITIONAL` hasta que el
   portón corra.

Permitir trabajo paralelo únicamente cuando los carriles sean independientes,
usando `paralelizar` para comprobar la independencia, registrar claims y
sintetizar.
Un verificador no recibe la conclusión que debe producir.

## Recuperación

Corregir mientras aparezcan hipótesis nuevas y progreso verificable. Ante el
mismo fallo sin nueva hipótesis, restaurar, consultar al humano y solicitar
Autopsia postejecución.

## Salida

```text
CRISOL_ID=...
PLAN=PASS|BLOCK
ARCHITECTURE=PASS|BLOCK|UNKNOWN
COLLISION=NONE|FOUND|UNKNOWN
IMPLEMENTATION=PASS|FAIL|NOT_RUN
VERIFICATION=PASS|FAIL|UNKNOWN
CLOSURE=FINAL|CONDITIONAL|BLOCKED
RECEIPT=...
```


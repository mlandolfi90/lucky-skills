---
name: crisol
description: Orquestar calidad incorporada para un cambio que afecta contratos, arquitectura o varias unidades. Usar cuando el humano pida Crisol o el fast path resulte insuficiente.
---

# Crisol

Coordinar un ciclo de cambio con criterio central y verificación independiente.

## Invariantes

- Mantener plan, criterio y diálogo humano en la sesión madre.
- Delegar solo carriles acotados con artefactos y contexto suficiente.
- Confirmar TARGET antes del carril escritor.
- No usar Crisol para una observación sin diagnóstico ni para un microfix que
  cabe de forma segura en una sola unidad.

## Carriles

1. **Planificar:** fijar resultado, alcance, pruebas y rollback.
2. **Arquitectura:** descubrir, ubicar y emitir dictamen.
3. **Colisiones:** resolver rutas, símbolos, contratos y criterios.
4. **Construir:** implementar de forma atómica y factorizada.
5. **Verificar:** probar comportamiento, regresiones, SOLID y fronteras.
6. **Cerrar:** emitir cierre final o condicional.

Permitir trabajo paralelo únicamente cuando los carriles sean independientes.
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


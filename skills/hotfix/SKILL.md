---
name: hotfix
description: Coordinar una corrección urgente de un fallo operativo. Usar cuando algo está roto en un TARGET confirmado y se necesita restaurar servicio con validación y rollback inmediatos.
---

# Hotfix

Restaurar el comportamiento esperado sin relajar control humano.

## Gates de entrada

- Confirmar incidente, diagnóstico, impacto y TARGET operativo exacto.
- Definir rollback antes de escribir.
- Consultar colisiones y cambios activos; ante `COLLISION=FOUND`, coordinar
  antes de escribir.
- No usar urgencia para omitir evidencia o autoridad.

## Ejecutar

1. Reducir el cambio al mecanismo necesario para restaurar servicio.
2. Preparar y probar fuera del estado activo cuando sea posible.
3. Aplicar al TARGET autorizado.
4. Verificar señal técnica y comportamiento del usuario.
5. Revertir si la señal no mejora.
6. Registrar seguimiento: cierre definitivo, cierre condicional o promoción a
   Crisol.

## Salida

```text
CHANGE_ID=<el de cambio>
CHANGE_KIND=HOTFIX
INCIDENT=...
TARGET=...
IMPACT=...
TESTS=PASS|FAIL|UNKNOWN
ROLLBACK=READY|APPLIED|UNAVAILABLE
FOLLOW_UP=NONE|QUALITY|REFACTOR|CRISOL
RECEIPT=...
```

`cierre` toma `CHANGE_ID`, `TESTS` y `ROLLBACK` de esta salida tal cual;
`FOLLOW_UP=CRISOL` es la entrada de `crisol`.

Crear commit o push únicamente dentro de la autorización explícita.


---
name: hotfix
description: Coordinar una corrección urgente de un fallo operativo. Usar cuando algo está roto en un TARGET confirmado y se necesita restaurar servicio con validación y rollback inmediatos.
---

# Hotfix

Restaurar el comportamiento esperado sin relajar control humano.

## Gates de entrada

- Confirmar incidente, diagnóstico, impacto y TARGET operativo exacto.
- Definir rollback antes de escribir.
- Consultar colisiones y cambios activos.
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
CHANGE_KIND=HOTFIX
INCIDENT=...
TARGET=...
IMPACT=...
VALIDATION=PASS|FAIL|UNKNOWN
ROLLBACK=READY|APPLIED|UNAVAILABLE
FOLLOW_UP=NONE|QUALITY|REFACTOR|CRISOL
RECEIPT=...
```

Crear commit o push únicamente dentro de la autorización explícita.


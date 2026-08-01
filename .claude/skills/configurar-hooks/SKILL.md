---
name: configurar-hooks
description: Preparar hooks lifecycle asesores para el harness activo. Usar al instalar o revisar automatización de eventos; nunca habilitar enforcement ni escribir configuración sin autorización.
---

# Configurar hooks

Adaptar eventos comunes sin fingir que todos los harnesses ofrecen lo mismo.

## Contrato común

Mantener lógica compartida para eventos:

- `SESSION_START`
- `BEFORE_WRITE`
- `AFTER_WRITE`
- `BEFORE_PUSH`
- `AFTER_FAILURE`
- `SESSION_END`

El handler asesor devuelve observaciones y siempre conserva la decisión humana.
Debe ser idempotente, acotado en tiempo y no contener secretos.
El runtime autónomo viaja en `scripts/`; no depende del checkout del catálogo
ni persiste el payload bruto del harness.

## Adaptar

1. Detectar un único harness activo.
2. Generar una propuesta específica:
   - Claude Code: fusionar el bloque `hooks` en
     `.claude/settings.json`; no crear `.claude/hooks.json`.
   - Codex: fusionar `.codex/hooks.json`, usar handlers `command` y declarar
     `AFTER_FAILURE` no soportado.
   - Claude.ai: `UNSUPPORTED`; no inventar hooks.
3. Mostrar rutas, eventos, comandos y diff exactos.
4. Exigir TARGET y autorización antes de instalar o fusionar configuración.
5. Dejar al humano la revisión o confianza que exija el harness.
6. Mantener v1 en `ADVISORY`. Enforcement requiere otra versión y una decisión
   humana explícita; no existe un toggle oculto.

## Salida

```text
HARNESS=...
HOOK_SUPPORT=SUPPORTED|PARTIAL|UNSUPPORTED
MODE=ADVISORY
EVENTS=...
TARGET=...
PLAN_HASH=...
WRITE_GATE=PASS|BLOCK
RECEIPT=...
```

Ningún hook sustituye Sextante, TARGET, Collision Map o síntesis de la sesión
madre.

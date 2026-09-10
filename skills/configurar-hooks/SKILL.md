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
`SESSION_START` recuerda el orden de arranque de `cargar-reglas` (reglas,
`ley-viva`, `sextante`); no lo ejecuta.
Debe ser idempotente, acotado en tiempo y no contener secretos.
El runtime autónomo viaja en `scripts/`; no depende del checkout del catálogo
ni persiste el payload bruto del harness.

## Hooks globales

Los hooks lifecycle de arriba son del repo y viajan con la adopción. Hay
otros dos que son del usuario en Claude Code: corren con cualquier cwd y se
instalan en `~/.claude/hooks/` con su entrada en `~/.claude/settings.json`.
Como `~/.claude` guarda credenciales y no puede ser repo, su fuente de verdad
es el catálogo y la copia instalada es byte a byte la de la skill adoptada;
se compara por hash y, si difiere, se reinstala desde la skill.

- `ley-viva-aviso.py` (`SessionStart`; `UserPromptSubmit` con
  `--throttle 900`): vive en `ley-viva`, `scripts/`.
- `custodiar-skills.py` (`PreToolUse`, matcher
  `Edit|Write|MultiEdit|NotebookEdit`): vive acá, en `scripts/`. Convierte
  la edición de una skill (`SKILL.md` o `manifest.env` bajo `skills/`, o
  cualquier archivo bajo `.claude/skills/`) en un pedido de permiso
  (`permissionDecision: ask`), y hace lo mismo con una escritura al Taller
  desde una sesión que no corre en él. No bloquea; una escritura por shell
  no pasa por acá, límite declarado. Dónde está el Taller lo declara la
  máquina, no el script: variable `LUCKY_TALLER` o `custodia.env` junto a la
  copia instalada (plantilla `scripts/custodia.env.example`); sin
  declaración esa mitad no opina. Pruebas sin red en
  `tests/conformance/test_hooks_globales.py`.

Instalar o cambiar su entrada en `settings.json` sigue el paso 4 de Adaptar:
TARGET y autorización, diff a la vista. Medido el 2026-09-10: los dos vivían
solo en disco, sin historial ni prueba en CI (lo midió lucky-tool-netbox).

## Adaptar

1. Detectar un único harness activo.
2. Generar una propuesta específica:
   - Claude Code: fusionar el bloque `hooks` en
     `.claude/settings.json`; no crear `.claude/hooks.json`.
   - Codex: fusionar `.codex/hooks.json`, usar handlers `command` y declarar
     `AFTER_FAILURE` no soportado.
   - Claude.ai: `UNSUPPORTED`; no inventar hooks.
3. Mostrar rutas, eventos, comandos y diff exactos.
4. Exigir TARGET y autorización antes de instalar o fusionar configuración:
   la fusión se ejecuta como transacción de `adopcion`, que archiva lo previo
   y valida el resultado (por eso esta skill la requiere).
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

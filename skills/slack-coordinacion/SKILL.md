---
name: slack-coordinacion
description: Se mudó a enlazar-agentes (canal slack) el 2026-10-11 y ya no coordina nada. Usar sólo si una sesión la encuentra adoptada, para pasarse a enlazar-agentes.
---

# Coordinación por Slack — se mudó

Desde el 2026-10-11 esta skill no coordina nada. Sus reglas viven en
`enlazar-agentes`, como el canal `slack` de su registro
(`references/canales/slack.md`), sin cambios de fondo.

Lo pidió la operadora el 2026-10-11: «slack coordinacion se abserve dentro de
enlazaragentes. se avisa sus cambios.»

## Por qué

Slack es uno de varios canales entre sesiones. El directo y el buzón no
tenían skill, y cada canal falla donde otro cubre. `enlazar-agentes` los junta
en un registro, y se usan solos o combinados.

## Qué hacer

1. Donde se usaba esta skill, usar `enlazar-agentes slack`. Las reglas son
   las mismas.
2. Para tener Slack por defecto en un proyecto, poner `CANALES=slack` en su
   `REGLAS.md`.
3. Actualizar esta skill trae `enlazar-agentes`: la pide en su `REQUIRES`.
4. Una copia personal en `~/.claude/skills/slack-coordinacion` tapa a la
   adoptada y no se actualiza sola: la retira su humano.

## Salida

```text
MUDADA_A=enlazar-agentes@1.0.0 (canal slack)
```

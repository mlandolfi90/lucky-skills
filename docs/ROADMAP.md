# Escalera de construcción

`ESTADO=PROTOTIPO`
`VERSION=0.1.0-prototype.1`

Las seis fases tienen implementación y pruebas de conformidad. Ninguna está
publicada: falta la propuesta SemVer, el manifiesto y el tag vía
`publicar-skill` (D-060, D-061). Cada fase declara abajo su estado real.

Este archivo describe el alcance construido, no el orden de trabajo pendiente.
Antes de dar por cerrada cualquier fase, corroborar contra el código —
`python -m pytest -q` y `python adapters/reference_python/run_validate_suite.py`.

## Fase 1 — Núcleo y Sextante

`OBJETIVO=ATERRIZAJE_VERIFICABLE`
`ESTADO=IMPLEMENTADO`

- Contrato portable y vocabulario canónico.
- Estado local, remoto, runtime y capacidades actuales.
- Resumen corto, comprobante inmutable y gates relevantes.
- Adaptador de referencia y conformidad Codex.

## Fase 2 — Adopción

`OBJETIVO=CREAR_LIFECYCLE_EXPLICITAMENTE`
`ESTADO=IMPLEMENTADO`

- Declarar capacidades y precondiciones de la skill de adopción.
- Crear el árbol normalizado solo con autorización.
- Inicializar y corroborar `STATE-MAP`; registrar autoría.
- No instalar adaptadores de harness que el proyecto no usa.

## Fase 3 — Arquitectura fragmentada

`OBJETIVO=CRITERIO_HEXAGONAL_CONSULTABLE`
`ESTADO=IMPLEMENTADO`

- Descubrimiento estructural, ubicación, fronteras, puertos y adaptadores.
- SOLID, responsabilidad única, atomicidad y factorización como gates locales.
- Skills pequeñas por tarea; la sesión madre conserva el criterio.
- Collision Map asistido por índice de codebase cuando exista.

## Fase 4 — Ciclo de cambio y calidad

`OBJETIVO=CALIDAD_INCORPORADA`
`ESTADO=IMPLEMENTADO`

- Observación, diagnóstico, microfix, hotfix, feature, quality, refactor y
  migration con transiciones explícitas.
- Microfix rápido y comprobable; acumulación y promoción posterior.
- Crisol, cierre condicional y rollback por commit.
- Autopsia postejecución con subagente primero; la sesión madre actúa como
  fallback cuando no haya agentes disponibles.
- TARGET siempre humano; autorización continua exige alcance explícito.

## Fase 5 — Hooks portables

`OBJETIVO=AUTOMATIZAR_SIN_OCULTAR_CRITERIO`
`ESTADO=IMPLEMENTADO`

- Contratos de evento independientes del harness.
- Modo asesor primero; enforcement solo donde se declare.
- Hooks mínimos, idempotentes, observables y desactivables por adaptación.
- Ningún hook sustituye autorización humana ni síntesis de la sesión madre.

## Fase 6 — Distribución y actualización

`OBJETIVO=PROPAGACION_CONTROLADA`
`ESTADO=IMPLEMENTADO_SIN_PUBLICAR`

- Catálogo versionado y manifiesto de adopción.
- Actualización con diff, compatibilidad, canary y rollback.
- Distribución a repos adoptantes sin copiar estado local.
- Migración del árbol versionado a `lucky-skills`; nunca trasladar este `.git`.

## Prioridad de harness

`ORDEN=CLAUDE_CODE,CLAUDE_AI,CODEX,OTROS`

El núcleo sigue siendo portable. Cada adaptador existe solo cuando el harness
en uso lo necesita y declara degradaciones sin fingir equivalencia.

Soporte de hooks verificado contra documentación del host:

| Harness | `HOOK_SUPPORT` | Destino | Degradación declarada |
|---|---|---|---|
| Claude Code | `SUPPORTED` | `.claude/settings.json` | ninguna |
| Codex | `PARTIAL` | `.codex/hooks.json` | `AFTER_FAILURE` (Codex no emite evento de fallo de tool) |
| Claude.ai | `UNSUPPORTED` | — | sin superficie de hooks (D-075) |

El cierre de turno se llama `Stop` en Codex y `SessionEnd` en Claude Code; ambos
normalizan a `SESSION_END`. Suscribirse a un evento que el host no emite instala
un hook que nunca dispara, así que las plantillas se comprueban contra el
vocabulario real de cada host en `tests/conformance/test_hooks.py`.

---
name: arquitectura-descubrir
description: Reconstruir la arquitectura real de un repositorio sin escribir. Usar antes de ubicar módulos, juzgar fronteras o planear cambios cuando la estructura no esté corroborada.
---

# Descubrir arquitectura

Reconstruir la forma observable del repositorio antes de aplicar un modelo.

## Invariantes

- Trabajar en solo lectura.
- Usar el aterrizaje vigente de Sextante.
- Tratar README y documentos como declaraciones, no como realidad.
- Preferir el grafo de Codebase Memory cuando esté expuesto; comprobar su
  cobertura. Usar búsqueda y lectura directa cuando falte cobertura.
- No convertir nombres de carpetas en capas sin comprobar dependencias.

## Flujo

1. Identificar lenguajes, entry points, unidades desplegables y comandos reales.
2. Trazar llamadas e importaciones de mayor impacto.
3. Reconocer dominio, casos de uso, puertos, adaptadores de entrada y salida,
   infraestructura e interfaz.
4. Señalar ciclos, archivos grandes, responsabilidades mezcladas y seams.
5. Contrastar el mapa con pruebas, configuración y runtime observable.
6. Registrar evidencia proporcional de tier: canales de E/S que comparten
   lógica, dominio que necesita pruebas sin infraestructura, cambio de
   infraestructura previsto o extensión paralela. No prescribir hexagonal
   desde nombres o tamaño.
7. Separar hechos, inferencias e incógnitas.

## Veredicto

```text
ARCHITECTURE_STATE=CORROBORATED|PARTIAL|UNKNOWN
STYLE=HEXAGONAL|MIXED|OTHER|UNKNOWN
TIER_EVIDENCE=...
ENTRY_POINTS=...
BOUNDARIES=...
PORTS=...
ADAPTERS=...
HOTSPOTS=...
UNCERTAINTIES=...
EVIDENCE=...
```

Persistir un mapa solo cuando el humano autorice documentación. Una exploración
no crea por sí misma nuevas carpetas ni refactors.

## Delegación

Permitir subagentes únicamente para sondas aisladas de solo lectura. Solo la
sesión madre integra evidencias y emite `ARCHITECTURE_STATE` y `STYLE`; un
subagente no promueve evidencia parcial ni conserva el veredicto final. En
contexto subagente, devolver evidencia acotada sin completar `Veredicto`.

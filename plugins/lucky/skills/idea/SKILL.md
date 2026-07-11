---
name: idea
description: >-
  Parking de ideas — captura UNA idea sin descarrilar el trabajo. Destino:
  docs/IDEAS.md SOLO si git rev-parse resuelve DESDE el cwd (jamás buscar
  repos vecinos/subcarpetas); sin repo git → ~/.claude/IDEAS-GLOBAL.md.
  Disparar cuando el usuario diga "anotá esto", "se me ocurrió",
  "idea:", "no quiero olvidar", o mencione una idea/variante/mejora PARA
  DESPUÉS a mitad de otra tarea. "/idea" sin argumentos = mostrar las últimas
  10 capturadas. NO disparar si pide implementarla YA (eso es trabajo normal),
  ni para tareas/recordatorios (sistema de tasks), ni para preferencias
  personales (eso es memoria). Captura → confirma en UNA línea → vuelve al
  trabajo de inmediato.
allowed-tools: Bash, Read, Write, Grep
---

# /idea — parking lot (nano)

Capturar sin descarrilar. El enemigo es perder la idea; el segundo enemigo es
perseguirla ahora.

## Capturar (cuando llega una idea)

1. Destilar a UNA línea: `YYYY-MM-DD · <idea> · <contexto-sin-secretos>`.
   Sin valores reales de credenciales/tokens/passwords — nombres de variable,
   valores ficticios o `<REDACTED>`.
2. Destino, en orden (fail-open, JAMÁS responder "no pude"):
   - **repo actual = lo que `git rev-parse --show-toplevel` resuelve DESDE el
     directorio de trabajo** (una carpeta suelta SIN `.git` NO es repo, y
     **PROHIBIDO salir a buscar repos en subcarpetas o vecinos** — si el cwd
     no resuelve, el escalón es el GLOBAL; hallazgos de cumplimiento
     2026-07-09: primero `docs/IDEAS.md` huérfano en carpeta contenedora,
     después captura+push a un repo VECINO que nadie pidió) →
     `docs/IDEAS.md` en ESA raíz (crearlo si falta, con header de formato);
   - sin repo git → `~/.claude/IDEAS-GLOBAL.md` (el escalón global; ahí
     anotá también de qué carpeta/tema vino la idea);
   - sin filesystem → devolver la línea formateada para que el humano la copie.
3. **Dedup:** `grep` por las palabras clave de la idea en el archivo destino;
   si ya existe → "ya estaba anotada (fecha)" y NO duplicar.
4. **Respaldo** (solo si hay repo): `git add docs/IDEAS.md` (SOLO ese archivo,
   NUNCA `-A` ni `.`) → `git commit -m "idea: <resumen-corto>"` → `git push`.
   Push falla → avisar en una línea y seguir (el commit local preserva).
5. **Volver al trabajo:** confirmar en UNA línea ("💡 anotada: …") y retomar
   EXACTAMENTE lo que se estaba haciendo. PROHIBIDO expandir la idea, opinar
   sobre ella, investigarla u ofrecer implementarla — el Crisol las lista al
   cierre de cada corrida (§Parking) y ahí el humano decide.

## Leer (`/idea` sin argumentos)

Mostrar las últimas 10 entradas del archivo que corresponda (repo o global),
tal cual. Nada más.

---

**Fuente de verdad: `github.com/mlandolfi90/lucky-skills` · esta copia = tag
`v1.37.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags
https://github.com/mlandolfi90/lucky-skills.git`), seguir la del repo e informar
al humano.

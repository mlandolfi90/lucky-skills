---
name: idea
description: >-
  Parking de ideas — captura UNA idea en docs/IDEAS.md sin descarrilar el
  trabajo. Disparar cuando el usuario diga "anotá esto", "se me ocurrió",
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
   - repo actual → `docs/IDEAS.md` (crearlo si falta, con header de formato);
   - sin repo → `~/.claude/IDEAS-GLOBAL.md`;
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
`v1.16.0` (cache local, NO la ley).** Ley viva: con red, si el repo tiene un tag
mayor (`git ls-remote --tags`), seguir la del repo e informar al humano.

---
name: podar-v2
description: Inventariar y retirar restos de enforcement v2 (hooks, gates, instalaciones) de los ámbitos que ya se rigen por v3. Usar durante la convivencia v2/v3 y al abandonar v2.
---

# Podar v2

Que los ámbitos gobernados por v3 dejen de pagar peaje a los vigilantes de v2
— sin romper los ámbitos donde v2 sigue viva.

## Invariantes

- Primero inventario, después tijera: cada resto v2 se lista con ruta y
  ámbito antes de tocar nada — hooks, skills instaladas, plugins, referencias
  en configuración global o del repo.
- Dos ámbitos, dos reglas:
  - **Repo**: podable cuando el repo declara gobernanza v3 (`.lifecycle/`
    con STATE-MAP corroborable).
  - **Usuario (global)**: un hook global muerde a todos los proyectos; se
    poda únicamente cuando ningún proyecto siga rigiéndose por v2, con
    decisión humana explícita. Mientras convivan, se declara `BLOCKED` y no
    se toca.
- Todo lo podado se archiva antes de retirarse (restauración posible); nada
  se elimina en silencio.
- La poda retira instalaciones, jamás la fuente: el repo de v2 no se toca.
- La compuerta es corta: un renglón por resto, con su destino.

## Flujo

1. Inventariar restos v2 en el ámbito pedido: instalaciones de skills,
   plugins de enforcement, hooks y sus referencias en configuración.
2. Clasificar cada resto por ámbito (repo | usuario) y podabilidad.
3. Emitir el plan corto y esperar aprobación.
4. Archivar y retirar lo aprobado; dejar recibo con lo archivado.
5. Verificar que el ámbito quedó sin peaje v2 y que los ámbitos v2 vivos no
   fueron tocados.

## Salida

```text
REMNANTS_FOUND=n
SCOPE=REPO|USER
PRUNED=n
ARCHIVED_TO=<ruta>
BLOCKED=<restos en convivencia|NONE>
RESULT=CLEAN|PARTIAL|BLOCKED
```

---
name: ley-viva
description: Comprobar al inicio de sesión que las skills adoptadas siguen vigentes contra el catálogo publicado, y avisar antes de trabajar si hay versión nueva. Nunca actualiza por su cuenta.
---

# Ley viva

Que ningún repo trabaje con gobernanza vencida sin saberlo.

## Fuente

```text
CATALOG_SOURCE=github.com/mlandolfi90/lucky-skills
REF=último tag skill-<id>-v* publicado; sin tags, el manifiesto en la rama default
```

La fuente es una línea mutable: cuando el catálogo migre de repo, cambiarla
es un PATCH de esta skill.

## Invariantes

- Se ejecuta al inicio de sesión en un repo adoptante, antes del trabajo.
  Donde el harness soporte hooks de inicio, el hook la recuerda.
- Compara lo adoptado (`.lifecycle/state/skills/*.env`) contra lo publicado
  en el catálogo, con la semántica SemVer de la casa: PATCH/MINOR nuevo →
  actualización fluida disponible; MAJOR nuevo → adaptación requerida.
- Solo avisa: la transición la ejecutan sincronizar y adopción con sus
  propias compuertas. Avisar no es actualizar.
- Sin acceso al catálogo, la vigencia es `UNKNOWN` y se declara: se trabaja
  con lo adoptado (que está instalado y verificado por huella), pero jamás
  se afirma "al día" sin haber comprobado.
- El aviso es corto: una línea por skill desactualizada, con su salto.

## Flujo

1. Enumerar las skills adoptadas del repo y sus versiones.
2. Resolver el catálogo a su referencia vigente.
3. Comparar versión por versión y clasificar cada salto.
4. Avisar antes de que el trabajo empiece; registrar la comprobación.

## Salida

```text
CATALOG=<repo@ref|UNREACHABLE>
ADOPTED=n
CURRENT=n
UPDATE_AVAILABLE=<skill@salto,...|NONE>
ADAPTATION_REQUIRED=<skill@salto,...|NONE>
CURRENCY=VERIFIED|UNKNOWN
```

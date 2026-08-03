---
name: publicar-skill
description: Validar y publicar una versión de una skill del catálogo. Usar al promover cambios terminados; propone SemVer, ejecuta gates y crea commit o tag solo con autorización.
---

# Publicar skill

Convertir un cambio cerrado en una versión consumible.

## Invariantes

- Publicar una skill por transacción.
- Exigir cierre y calidad verificables.
- Mantener una sola versión vigente en el árbol; usar Git para historial.
- No modificar repositorios adoptantes; Sincronizar posee esa coordinación.
- No crear commit, tag o push sin autorización explícita para cada acción.

## Flujo

1. Validar nombre, frontmatter, `manifest.env`, recursos y dependencias.
   Para una skill nueva, verificar además su colisión de responsabilidad
   contra el catálogo: ninguna skill vigente cubre el mismo disparador, y
   todo solapamiento parcial (por ejemplo, profundizar un carril de otra)
   queda declarado con su justificación. Una skill que ignora su colisión
   nace vencida, igual que un diseño.
2. Ejecutar conformidad y canary de la versión propuesta en cada harness
   soportado.
3. Comparar con la versión vigente.
4. Proponer:
   - `INITIAL`: nacimiento. Una skill que nunca se publicó se sella en la
     versión que declara; no se bumpea. Lo determina la ausencia de su tag,
     no la pide quien publica.
   - `PATCH`: corrección compatible.
   - `MINOR`: capacidad compatible.
   - `MAJOR`: contrato incompatible.
5. Mostrar versión, diff, gates y `PLAN_HASH`.
6. Tras confirmación, actualizar el manifiesto, repetir el canary sobre el
   resultado y ejecutar únicamente las acciones Git autorizadas.
7. Registrar por separado quién autorizó release, commit, tag y push.
8. Emitir comprobante de release y entregar el relevo a Sincronizar.

Si commit ya ocurrió y tag o push son rechazados, no ocultar el avance ni
forzar el remoto: emitir `HUMAN_REQUIRED` con la razón exacta.

## Salida

```text
SKILL=...
FROM_VERSION=...
TO_VERSION=...
IMPACT=INITIAL|PATCH|MINOR|MAJOR
QUALITY=PASS|FAIL
PLAN_HASH=...
COMMIT=<SHA>|NO
TAG=<TAG>|NO|REJECTED
PUSH=PUSHED|REJECTED|NOT_ATTEMPTED|NO
RELEASE=READY|PUBLISHED|HUMAN_REQUIRED|BLOCKED
REASON=...
RECEIPT=...
```

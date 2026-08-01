---
name: mapear-despliegue
description: Mantener el mapa de accesos del deploy; qué credenciales se necesitan, dónde viven en el gestor y qué caminos usa la promoción. Nombres siempre, valores jamás.
---

# Mapear despliegue

Que cualquier sesión encuentre todos los accesos de un deploy sin que nadie
pegue una clave.

## Invariantes

- El mapa contiene nombres y ubicaciones: gestor, proyecto, entorno y nombre
  de cada secreto. Jamás un valor — el mapa se versiona con el repo y un
  valor versionado es fuga.
- El gestor es configurable por proyecto: el mapa declara cuál y en qué
  modo; la skill no asume ninguno.
- Los valores se resuelven en runtime contra el gestor declarado, dentro del
  patrón de custodiar-secretos: proceso único, sin transcripción.
- Un deploy sin mapa completo se frena: mejor un mapa que falta que una
  clave pegada en el chat.
- El mapa vive en `.lifecycle/local/` — fuera de git por diseño: aun sin
  valores, revela topología (proyectos, apps, endpoints). Versionarlo o
  exportarlo a otra sesión o máquina es un acto explícito del humano, nunca
  un default.
- El mapa se actualiza cuando el stack cambia; un mapa viejo es drift y lo
  audita documentar.

## Plantilla — `.lifecycle/local/DESPLIEGUE.env` (fuera de git por diseño)

```text
FORMAT_VERSION="1"
# TARGET del deploy, en la gramática de la casa: paas:<proyecto>/<app>@<env>,
# docker-local o pc-local. Cada deploy lo lee de acá; nadie lo asume.
DEPLOY_TARGET="<paas:proyecto/app@env|docker-local>"
SECRETS_MANAGER="<gestor:modo — ej. infisical:api, vault:api, env:local>"
MANAGER_PROJECT="<proyecto-en-el-gestor>"
MANAGER_ENV="dev|prod"
# Un secreto por línea: SOLO su nombre y ruta en el gestor
SECRET_<USO>="<ruta/NOMBRE-EN-EL-GESTOR>"
PIPELINE="<gh-actions:workflow|otro>"
DEPLOY_PLATFORM="<coolify:app|otro>"
HEALTH_ENDPOINT="<url de verificación de aterrizaje>"
ROLLBACK="<mecanismo>"
```

## Flujo

1. Inventariar qué necesita la promoción: secretos, pipeline, plataforma,
   verificación, rollback.
2. Registrar cada secreto por nombre y ubicación en el gestor; verificar que
   el nombre existe sin leer su valor.
3. Guardar el mapa en `.lifecycle/local/`; compartirlo (export a otra
   sesión, otra máquina o al repo) solo con decisión explícita del humano.
4. Al desplegar, la sesión resuelve los accesos desde el mapa; ningún valor
   toca el chat ni el mapa.

## Salida

```text
MAP=DESPLIEGUE.env
SECRETS_MAPPED=n
VALUES_IN_MAP=0
VERIFIED_NAMES=n
RESULT=COMPLETE|INCOMPLETE
```

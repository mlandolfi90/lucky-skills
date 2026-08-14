---
name: sincronizar
description: Comparar el catálogo con repositorios registrados y coordinar actualizaciones. Usar tras publicar o por petición explícita; propone adaptación antes de cualquier escritura remota.
---

# Sincronizar

Coordinar versiones sin convertir un lote en una transacción global.

## Invariantes

- Leer `registry/repos/<repo-id>.env`; nunca guardar credenciales.
- Corroborar el estado dentro de cada repositorio.
- Mantener clasificación y autoridad en la sesión madre.
- Permitir subagentes solo para análisis remoto de solo lectura y con salida
  normalizada.
- Ejecutar Adopción por repositorio después de autorización.

## Comparar

Clasificar cada repositorio:

- `CURRENT`: versión vigente.
- `READY_FAST`: transición compatible sin adaptación conocida.
- `NEEDS_ADAPTATION`: instalación inicial o cambio de contrato.
- `BLOCKED`: el repositorio no admite la transición, y eso se sabe.
- `UNDETERMINED`: no se pudo establecer el estado. No es un veredicto sobre
  el repositorio: es la medición confesando que falló. Nunca autoriza aplicar.

Un fallo de medición jamás se reporta como `BLOCKED`. Cuando aparece
`UNDETERMINED` se emite además la causa cruda, para que un humano entienda qué
pasó sin volver a correr el plan.

Mostrar primero:

```text
SKILL=...@...
REPOSITORIES=...
CURRENT=...
READY_FAST=...
NEEDS_ADAPTATION=...
BLOCKED=...
UNDETERMINED=...
UNDETERMINED=<repo-id>|<motivo>|<causa cruda>   (una por repositorio sin medir)
BATCH_PLAN=...
BRANCH_PREFIX=...
BRANCH=<repo-id>|<rama-exacta>
WRITE_GATE=BLOCK
```

## Aplicar

Aceptar selección puntual o autorización continua con repositorios, acciones,
ramas y fin exactos. El prefijo y las ramas propuestas forman parte del
`BATCH_PLAN`; no pueden elegirse después de confirmarlo. Para cada repositorio
autorizado:

1. Obtener la rama remota vigente.
2. Crear una rama aislada.
3. Ejecutar Sextante y Adopción.
4. Validar y crear el commit autorizado.
5. Hacer push normal y abrir PR o MR si existe capacidad.

Nunca usar force-push. Ante rechazo, emitir `PUSH=REJECTED` y
`ACTION=HUMAN_REQUIRED`; continuar otros casos seguros y agrupar consultas.

## Resultado

La atomicidad es por repositorio. Emitir `COMPLETE`, `PARTIAL` o `BLOCKED` y un
comprobante independiente por destino. Cada comprobante conserva el
autorizador del lote y del push, la identidad Git utilizada y, si aplica,
quién aceptó los riesgos.

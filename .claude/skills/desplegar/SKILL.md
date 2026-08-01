---
name: desplegar
description: Llevar un cambio cerrado a su entorno por promoción de CI, con prueba positiva de aterrizaje. Usar tras el cierre cuando el cambio debe llegar a un servidor o servicio.
---

# Desplegar

El deploy es una promoción, no un acto manual: commit → CI → build →
entorno. Y verde no es prueba — aterrizado sí.

## Invariantes

- Nada se copia a mano a un servidor: todo deploy viaja por la promoción
  declarada del repo (pipeline de CI, imagen, plataforma).
- El verde del pipeline no prueba el deploy: se exige prueba positiva de
  aterrizaje — el sha o artefacto servido por el entorno coincide con el
  commit esperado, leído del entorno, no del pipeline.
- Un paso de deploy condicionado se gatea a nivel de job, no de step: un
  deploy que no corrió debe reportar `skipped`, jamás `success`.
- TARGET confirmado antes de disparar; el entorno de destino se nombra,
  nunca se asume.
- Rollback declarado antes de disparar: redeploy de la versión anterior o
  el mecanismo que la plataforma provea.
- Un deploy rechazado o a medias no se reintenta a ciegas: se diagnostica
  con la evidencia del pipeline y del entorno.

## Flujo

1. Confirmar cierre del cambio y TARGET del entorno; resolver los accesos
   desde el mapa de despliegue del proyecto (`.lifecycle/local/DESPLIEGUE.env`) si existe —
   sin mapa, los accesos se nombran a mano, nunca se pegan.
2. Declarar el rollback disponible.
3. Disparar la promoción (push, tag o dispatch — lo que el repo declare).
4. Esperar el pipeline; ante `skipped` silencioso, tratarlo como fallo.
5. Verificar aterrizaje contra el entorno real: versión servida == commit
   esperado.
6. Declarar resultado y evidencia; capturar al saber lo aprendido si el
   deploy enseñó algo.

## Salida

```text
DEPLOY_TARGET=<entorno>
TRIGGER=CI
PIPELINE=GREEN|RED|SKIPPED
LANDED=VERIFIED|NOT_VERIFIED
EVIDENCE=<sha servido vs esperado>
ROLLBACK=<mecanismo>
```

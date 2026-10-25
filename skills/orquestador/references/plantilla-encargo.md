---
encargo: NNN
estado: abierto          # abierto | en-implementacion | en-revision | bloqueado | cambios | aprobado
vuelta: 1
creado: AAAA-MM-DD
carpeta: <ruta absoluta donde corre la hija; la comprueba al arrancar>
base: <commit del que parte; la madre lo escribe al lanzar>
hija: subagente          # subagente | sesion
revision: si             # si | no
modelo_trabajo: sonnet
esfuerzo_trabajo: high
modelo_revision: opus
esfuerzo_revision: high
sesion_id: ~             # sólo hija: sesion
plazo: ~                 # sólo hija: sesion, p. ej. 90m
cambios: ninguno         # cada apartamiento del default: qué, quién lo pidió, cuándo
---

# NNN: <título>

## Objetivo

<Una o dos frases. Qué tiene que ser verdad al terminar.>

## Contexto

<Sólo los hechos que la hija necesita, ya medidos: rutas, valores, estado
actual. Enlace al plan o al pedido del humano que cubre. Nombres de
secretos, nunca valores: este archivo se commitea.>

## Convenciones que rigen

- `CLAUDE.md`
- <`REGLAS.md`, el plan, un README, la guía de estilo del módulo>

Ante una duda de forma que estos archivos no resuelvan, la hija para y
devuelve la pregunta. No inventa.

## Alcance

- Puede tocar: <rutas>
- Puede ejecutar: <comandos o tipos de comando>
- No toca: <lo que queda fuera, aunque parezca relacionado>

## Criterios de hecho

- [ ] Chequeo barato: `<comando de segundos que declara el repo>` en verde.
- [ ] <verificable por la revisora sin creerle a la implementadora>
- [ ] <...>

## Preguntas para el humano

<Lo llena la hija si algo necesita una decisión que no es suya, y cierra
con ESTADO: bloqueado. La madre las lleva de a una. Debajo de cada una,
la madre anota la respuesta y la fecha.>

## Informe de la implementadora

<Lo llena la hija: qué hizo archivo por archivo, qué comandos corrió y su
resultado resumido, cada criterio cumplido o no con su evidencia, lo que
no pudo hacer y por qué, fricción de permisos. Sin valores de secretos.>

## Dictamen de la revisora — vuelta 1

<Lo pega la madre tal cual: la respuesta completa de la revisora. Cada
vuelta agrega su propia sección debajo; las anteriores no se borran.>

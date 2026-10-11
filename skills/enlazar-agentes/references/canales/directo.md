# Canal: directo

```text
CANAL=directo
VERSION=1.0.0
ORIGEN=herramientas del harness `SendMessage` y `ListAgents` (antes,
  `send_message` del gestor de sesiones de la app de escritorio); nombrado en
  el CLAUDE.md del espacio de trabajo («el directo (`SendMessage`, a una
  sesión abierta)»); fallas medidas el 2026-08-14 y el 2026-10-09
```

Para avisarle algo ahora a otra sesión de Claude que está abierta y aparece en
`ListAgents`.

## Cuándo

- El destino aparece en `ListAgents` y el aviso sirve ahora: un pedido, un
  acuse, una respuesta corta.
- Según el harness, `ListAgents` muestra las sesiones de esta máquina y,
  cuando hay conexión, las de la nube y las de Remote Control en otras
  máquinas. Una sesión en la nube recibe pero no puede contestar: su respuesta
  se lee en su transcript. Lo medido acá es sólo entre sesiones de esta
  máquina.
- No sirve para una sesión que no está abierta o que no aparece en
  `ListAgents`: ahí van `buzon` o `slack`.

## Reglas

- **El nombre es la dirección, y cambia.** Antes de mandar, mirar
  `ListAgents`: una sesión que se reabre vuelve con otro nombre. Para
  contestar un mensaje, se usa el `from` que trajo.
- **La primera línea se tiene que entender sola.** Es lo único que el humano
  del destino ve antes de abrir el mensaje.
- **No se lava un permiso.** No se le pide a otra sesión algo que a esta se le
  negó o se le bloqueó: eso es saltear la decisión del humano. Se le lleva al
  humano de esta sesión.
- **Lo que tiene que constar no va sólo por acá.** Se combina con `buzon` o con
  `slack`, y el aviso nombra el `MSG_ID` o el hilo.

## Garantías

- **«Éxito» quiere decir que la herramienta aceptó el envío.** No asegura que
  el mensaje llegó (ver **Fallas medidas**), y menos que su Claude lo leyó.
- **No deja constancia** en ningún repo.

## Fallas medidas

- **2026-08-14:** con `send_message` del gestor de sesiones de la app de
  escritorio (`mcp__ccd_session_mgmt__send_message`), reportó éxito y no
  entregó: dos envíos, uno en cada dirección, y no llegó ninguno. Con
  `SendMessage` no se midió si pasa lo mismo.
- **2026-10-09:** dio `ENOINBOX` con el nombre viejo de una sesión que se había
  reabierto con otro nombre. Con el nombre nuevo, sacado de `ListAgents`, llegó.

## Degradación

- Si el destino no aparece en `ListAgents` o el envío falla, se pasa a `buzon`,
  y también a `slack` si lo tienen que ver todos. Nunca se da por entregado.

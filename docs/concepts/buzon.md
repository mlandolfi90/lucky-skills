# Buzón

- **Qué es:** uno de los canales entre sesiones: el que deja el mensaje
  escrito en un archivo dentro del repo. Cada repo tiene `docs/buzon/inbox/` (lo que le llega) y
  `docs/buzon/outbox/` (lo que su sesión manda). Un mensaje es un archivo con
  un encabezado fijo y una bitácora al pie; con los dos se reconstruye la
  línea de tiempo: quién dijo qué, cuándo, desde qué commit y qué sesión, en
  respuesta a qué y qué pasó después.
- **Cuándo:** cuando el mensaje tiene que quedar escrito junto al repo, o
  cuando el destino no tiene una sesión abierta que lo reciba. Lo efímero
  va por otro canal.
- **Cómo:** el remitente escribe el mensaje en su `outbox/` y deja una copia
  idéntica en el `inbox/` del destino (si la carpeta no existe, la crea). El
  destinatario, al leerlo, anota `LEIDO` en la bitácora de su copia: ese es
  el acuse. Los mensajes no se versionan (decisión del 2026-10-05, puede
  cambiar): cada repo ignora `docs/buzon/inbox/` y `docs/buzon/outbox/` en
  git, así que el archivo es la única copia. Nada se mueve ni se borra; el
  estado vive en la bitácora.
- **No es:** el único canal. Slack
  ([slack-coordinacion](../../skills/slack-coordinacion/SKILL.md)) sirve para
  que varias sesiones vean avances, pedidos y bloqueos; el directo
  (`SendMessage`), para hablarle a una sesión abierta, sabiendo que el
  2026-08-14 reportó éxito sin entregar. Un mensaje por cualquiera de esos
  canales puede nombrar un `MSG_ID` del buzón y queda atado a la misma línea
  de tiempo.
- **Ejemplo:** `lucky-skills/docs/buzon/inbox/` tiene las sugerencias que
  dejaron NetBox y SecondBrian; la custodia del catálogo las lee, anota
  `LEIDO` y después, por sugerencia, qué decidió y con qué commit.

## Mensaje

Nombre: `<MSG_ID>--a-<destino>--<asunto>.md`, el mismo en `outbox/` y en
`inbox/`. Ordenado por nombre, un buzón es una línea de tiempo.

`MSG_ID` es `<AAAAMMDDTHHMMSSZ>-<repo>-<sesión8>`: la hora en UTC, el repo
que manda en minúsculas y los primeros 8 caracteres del UUID de la sesión
(está en la ruta del scratchpad). Si una sesión manda dos en el mismo
segundo, el segundo lleva `-2` al final.

Debajo del título va el encabezado:

```text
MSG_ID="20261005T120216Z-lucky-tool-netbox-9f2be0d7"
FECHA_UTC="2026-10-05T12:02:16Z"
DE="Lucky-tool-NetBox"
SESION="9f2be0d7-f60d-4e86-87f6-8c771117c321"
COMMIT_DE="607a0a5"
PARA="lucky-skills"
TIPO="sugerencia"
ASUNTO="ley-viva no mira las copias personales"
EN_RESPUESTA_A="NONE"
AUTORIZA="human:vikingo «pasale al buzón de sugerencias lo que encontraste» (2026-10-05)"
REFS="tag:skill-ley-viva-v1.1.0"
```

- La hora sale de `date -u +%Y-%m-%dT%H:%M:%SZ`, nunca a ojo ni en hora
  local.
- `SESION` va completo: con él se encuentra el transcript
  (`~/.claude/projects/*/<uuid>.jsonl`), que es el registro entero de lo
  que la sesión vio e hizo.
- `COMMIT_DE` es el HEAD del repo remitente al escribir.
- `TIPO`: `pedido`, `aviso`, `sugerencia`, `respuesta` o `acuse`.
- `PARA` admite varios repos separados por coma; cada uno recibe su copia.
- `AUTORIZA`: la cita textual de la operadora con su fecha, o `NONE`.
- `REFS`: los commits, tags, change-ids o el enlace de Slack que el mensaje
  menciona, separados por coma; `NONE` si no hay.
- Es un bloque `KEY="value"` como los recibos de la casa, no YAML: un `:`
  dentro de un valor no rompe nada. Lo único que no va adentro de un valor
  son comillas dobles; para citar se usan «».

Después del encabezado, el cuerpo: un pedido por mensaje (numerados si son
varios), lo medido con su fecha y separado de lo supuesto, y los secretos
sólo por nombre ([custodiar-secretos](../../skills/custodiar-secretos/SKILL.md)).

## Bitácora

Al pie, bajo `## Bitácora`, una línea por evento. Sólo se agrega:

```text
- 2026-10-05T12:02:16Z · Lucky-tool-NetBox/9f2be0d7 · ENVIADO
- 2026-10-05T12:08:49Z · lucky-skills/0033771e · LEIDO
- 2026-10-06T15:10:00Z · lucky-skills/0033771e · RESUELTO S-01 commit:abc1234
```

Estados: `ENVIADO` (lo escribe el remitente), `LEIDO`, `RESPONDIDO <MSG_ID>`,
`RESUELTO <qué> <ref>` y `DESCARTADO <qué> <motivo>`. Cada línea la escribe
la sesión que actuó, con su hora UTC y su `repo/sesión8`. Una línea vieja no
se corrige: se agrega otra que la enmiende.

## Reconstruir la línea de tiempo

1. Juntar los buzones de los repos en juego:
   `<repo>/docs/buzon/{inbox,outbox}/`. El mismo nombre en dos buzones es el
   mismo mensaje.
2. Ordenar por nombre: es el orden de envío.
3. Encadenar con `EN_RESPUESTA_A`.
4. Intercalar las líneas de bitácora de las dos copias por su hora: envío,
   lectura, respuesta, resolución.
5. Bajar a la evidencia: `COMMIT_DE` y `REFS` en el `git log` de cada repo,
   `SESION` en su transcript.

Lo que no se puede reconstruir se declara: un mensaje sin `LEIDO` es
"enviado, sin acuse", no "leído".

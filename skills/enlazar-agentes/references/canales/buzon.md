# Canal: buzon

```text
CANAL=buzon
VERSION=1.0.0
ORIGEN=pedido de la operadora del 2026-10-04: «dejarle las mejoras a lucky
  skill en un buzon de sugerencias para levantar la sesion luego»; convención
  del 2026-10-05 en lucky-skills (`docs/concepts/buzon.md`, commit 9ca833a)
```

Para que un mensaje quede escrito junto al repo, con lo necesario para
reconstruir después quién dijo qué, cuándo, desde qué commit y qué pasó
después.

## Cuándo

- El mensaje tiene que quedar escrito: un pedido, una sugerencia, una
  respuesta o un acuse que alguien va a querer leer después.
- El destino no tiene una sesión abierta que lo reciba.
- No sirve para un destino en otra máquina, que no ve este disco: ahí va
  `slack`.

## Reglas

- **Un mensaje es un archivo**, con el mismo nombre en el `outbox/` de quien lo
  manda y en el `inbox/` de cada destino, bajo `docs/buzon/` de cada repo. Si la
  carpeta del destino no existe, se crea.
- **Nombre:** `<MSG_ID>--a-<destino>--<asunto>.md`. Ordenado por nombre, un
  buzón es una línea de tiempo.
- **`MSG_ID`:** `<AAAAMMDDTHHMMSSZ>-<repo>-<sesión8>`: la hora en UTC, el repo
  que manda en minúsculas y los primeros 8 caracteres del UUID de la sesión
  (está en la ruta del scratchpad). Si una sesión manda dos en el mismo
  segundo, el segundo lleva `-2` al final.
- **Encabezado**, debajo del título, como bloque `KEY="value"`:

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
    (`~/.claude/projects/*/<uuid>.jsonl`), que es el registro entero de lo que
    la sesión vio e hizo.
  - `COMMIT_DE` es el HEAD del repo remitente al escribir.
  - `TIPO`: `pedido`, `aviso`, `sugerencia`, `respuesta` o `acuse`.
  - `PARA` admite varios repos separados por coma; cada uno recibe su copia.
  - `AUTORIZA`: la cita textual de la operadora, con su fecha, o `NONE`.
  - `REFS`: los commits, tags, change-ids o el enlace de Slack que el mensaje
    menciona, separados por coma; `NONE` si no hay.
  - No es YAML: un `:` dentro de un valor no rompe nada. Lo único que no va
    adentro de un valor son comillas dobles; para citar se usan «».
- **Cuerpo:** un pedido por mensaje (numerados si son varios), lo medido con su
  fecha y separado de lo supuesto, y los secretos sólo por nombre.
- **Bitácora**, al pie, bajo `## Bitácora`: una línea por evento, y sólo se
  agrega.

  ```text
  - 2026-10-05T12:02:16Z · Lucky-tool-NetBox/9f2be0d7 · ENVIADO
  - 2026-10-05T12:08:49Z · lucky-skills/0033771e · LEIDO
  - 2026-10-06T15:10:00Z · lucky-skills/0033771e · RESUELTO S-01 commit:abc1234
  ```

  Estados: `ENVIADO` (lo escribe el remitente), `LEIDO`, `RESPONDIDO <MSG_ID>`,
  `RESUELTO <qué> <ref>` y `DESCARTADO <qué> <motivo>`. Cada línea la escribe la
  sesión que actuó, con su hora UTC y su `repo/sesión8`. Una línea vieja no se
  corrige: se agrega otra que la enmiende. Nada se mueve ni se borra.
- **No se versiona** (decisión del 2026-10-05, puede cambiar): cada repo ignora
  `docs/buzon/inbox/` y `docs/buzon/outbox/` en git, así que el archivo es la
  única copia.

## Garantías

- **Deja constancia** junto al repo, con hora, sesión y commit.
- **No avisa:** el destino se entera cuando mira su `inbox/`. Si hace falta que
  se entere ahora, se combina con `directo` o con `slack`.

## Fallas medidas

- Nada obliga a que cada repo use la misma forma: lo sostiene este archivo.
- Hay repos que guardaban mensajes con otra forma, anterior a esta convención
  (sin `MSG_ID` ni bitácora).

## Degradación

- Si no se puede escribir en el repo del destino —está en otra máquina, o no
  hay acceso—, se declara. El mensaje queda en el `outbox/` con una línea de
  bitácora que lo dice, y se avisa por `slack`. Nunca se da por entregado.

## Flujo

### Mandar

1. Armar el `MSG_ID`.
2. Escribir el mensaje en el `outbox/` propio, con la bitácora en `ENVIADO`.
3. Dejar una copia idéntica en el `inbox/` de cada repo de `PARA`.

### Leer

1. Lo que no tiene `LEIDO` de esta sesión es lo nuevo.
2. Anotar `LEIDO` en la bitácora de esa copia: ese es el acuse.
3. Resolver con el humano de esta sesión, pedido por pedido: responder con un
   mensaje nuevo que lo cite en `EN_RESPUESTA_A` (`RESPONDIDO <MSG_ID>`),
   aplicarlo (`RESUELTO <qué> <ref>`), descartarlo (`DESCARTADO <qué>
   <motivo>`), o contestar qué falta medir.

### Reconstruir la línea de tiempo

1. Juntar los buzones de los repos en juego. El mismo nombre en dos buzones es
   el mismo mensaje.
2. Ordenar por nombre: es el orden de envío.
3. Encadenar con `EN_RESPUESTA_A`.
4. Intercalar las líneas de bitácora de las copias por su hora.
5. Bajar a la evidencia: `COMMIT_DE` y `REFS` en el `git log` de cada repo, y
   `SESION` en su transcript.

Lo que no se puede reconstruir se declara: un mensaje sin `LEIDO` es «enviado,
sin acuse», no «leído».

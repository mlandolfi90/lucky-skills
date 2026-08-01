# Contrato portable de comprobante Sextante v1

Este archivo define la salida y los gates del paquete autónomo. Se aplica junto
a los contratos de [configuración lifecycle](lifecycle-config-v1.md),
[State Map](state-map-v1.md) y
[huella local v3](local-fingerprint-v1.md). Un comprobante v1 contiene los 91
campos fijos definidos abajo, cero o más entradas `CAPABILITY_NNN` y ninguna
evidencia secreta.

## Serialización canónica

1. Codificar en UTF-8 sin BOM y usar únicamente saltos LF.
2. Emitir una línea `CLAVE=<cadena-JSON>` por valor. La clave cumple
   `^[A-Z][A-Z0-9_]*$`; el valor siempre es texto.
3. Serializar la cadena como JSON con Unicode sin convertir a ASCII. Escapar
   comillas, barra inversa y controles según JSON: `\"`, `\\`, `\n`, `\r`,
   `\t` o `\uXXXX`. Un salto de línea del valor nunca se vuelve una línea real.
4. No emitir comentarios, líneas vacías, claves duplicadas ni espacios fuera
   de la cadena JSON. Terminar también la última línea con LF.
5. Conservar el orden de emisión de las tablas. Después de `DECIDED_BY`, emitir
   `CAPABILITY_001` a `CAPABILITY_NNN`; emitir `RECEIPT_HASH` al final.
6. Calcular `RECEIPT_HASH` como SHA-256 hexadecimal minúsculo de los bytes UTF-8
   del documento canónico anterior, sin la línea `RECEIPT_HASH`. Las entradas
   de capacidad y cualquier extensión participan en el hash.

El validador v1 interpreta los campos por nombre y solo exige posicionalmente
que `RECEIPT_HASH` sea la última clave; no se debe inferir semántica por número
de línea. Al leer desde archivo, el límite es 1 000 000 bytes. Una extensión
desconocida se conserva y entra en el hash; si termina en `_AT_UTC`, también
debe ser un timestamp válido. Se rechaza cualquier clave que contenga
`SECRET`, `PASSWORD`, `TOKEN`, `CREDENTIAL` o `PRIVATE_KEY`.

## Tipos y enums

- `bool`: `TRUE | FALSE`.
- `hex16` / `hex64`: exactamente 16 / 64 caracteres `[0-9a-f]`.
- `version`: `[0-9A-Za-z][0-9A-Za-z._+-]{0,63}`.
- `utc`: ISO 8601 parseable, terminado en `Z` y con offset UTC.
- `source-result`:
  `ALIGNED | DRIFT | PARTIAL | STALE | NOT_APPLICABLE`.
- `evidence`:
  `VERIFIED_DIRECT | HUMAN_PROVIDED | DECLARED | UNKNOWN`.
- `component-state`: `LOADED | ABSENT | INVALID`.
- `actor`: prefijo `session:`, `agent:`, `human:` o `harness:`, seguido de un
  identificador no vacío; máximo 256 caracteres, sin CR, LF ni NUL.
- `human`: un `actor` cuyo prefijo es `human:`.
- `mother-session`: `session:mother` o `session:mother:<identificador>`.
- `count`: entero decimal entre 0 y 1 000 000.
- `max-age`: entero decimal entre 1 y 86 400 segundos.
- `opaque`: texto sin semántica inferida; usar el sentinel documentado cuando
  el dato no exista.

`RUNTIME_STATE`, `CAPABILITIES_STATE` y `LOCAL_SCAN_STATUS` son códigos
extensibles. `REMOTE_STATE` usa en v1: `EVIDENCE_EXPIRED`,
`GIT_UNAVAILABLE`, `LOCAL_BRANCH_UNAVAILABLE`, `MALFORMED_URL`,
`MULTIPLE_CANDIDATES`, `MULTIPLE_URLS`, `NETWORK_CONFIRMATION_REQUIRED`,
`NO_GIT`, `NO_REMOTE`, `OUTPUT_LIMIT`, `REF_NOT_FOUND`,
`REMOTE_RESPONSE_INVALID`, `SOURCE_CONFIRMATION_MISMATCH`, `TIMEOUT`,
`UNKNOWN_SELECTION`, `UNREACHABLE`, `UNSAFE_URL_COMPONENTS`,
`UNSUPPORTED_SAFE_TRANSPORT`, `URL_UNAVAILABLE` o `VERIFIED`.

## Campos fijos en orden de emisión

### Identidad, ejecución y workspace

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 1 | `RECEIPT_SCHEMA` | Fijo `1`. |
| 2 | `RECEIPT_ID` | `^sextante-[0-9A-Za-z._-]{1,128}$`; identifica este archivo inmutable. |
| 3 | `SKILL_VERSION` | `version` observada al inicio. |
| 4 | `SKILL_VERSION_SOURCE` | `opaque`; fuente de la versión inicial. |
| 5 | `SKILL_VERSION_FINISHED` | `version` observada al final o `UNAVAILABLE`. |
| 6 | `CONTRACT_VERSION` | Fijo `1`. |
| 7 | `ADAPTER_ID` | Identificador estable del adaptador; referencia: `reference-python`. |
| 8 | `ADAPTER_VERSION` | `version` del adaptador. |
| 9 | `HARNESS` | `opaque`; harness que ejecutó Sextante. |
| 10 | `EXECUTION_LEVEL` | `NATIVE | ADAPTED | DEGRADED | MANUAL`. |
| 11 | `INTENT` | `read | edit | push | deploy`. |
| 12 | `STARTED_AT_UTC` | `utc`; inicio de la observación. |
| 13 | `FINISHED_AT_UTC` | `utc`; fin, nunca anterior al inicio. |
| 14 | `WORKSPACE_ID` | `hex16`; primeros 16 hex de SHA-256 del texto de `WORKSPACE_PATH`. |
| 15 | `WORKSPACE_PATH` | Ruta resuelta del workspace observado. |

### Lifecycle y política de README

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 16 | `LIFECYCLE` | `ADOPTED | NOT_ADOPTED | INVALID`. |
| 17 | `CONFIG_STATUS` | `VALID | INVALID`; derivado de los tres componentes siguientes. |
| 18 | `POLICY_STATUS` | `component-state` de `SEXTANTE.env`. |
| 19 | `SOURCES_STATUS` | `component-state` de `SOURCES.env`. |
| 20 | `STATE_MAP_STATUS` | `component-state` de `STATE-MAP.env`. |
| 21 | `README_POLICY` | `IGNORE | DISCOVERY_ONLY | DECLARED_TRUST`. |
| 22 | `README_POLICY_SOURCE` | `DEFAULT | SESSION_OVERRIDE | SESSION_HUMAN` en el adaptador de referencia. |
| 23 | `README_POLICY_CONFIRMED_BY` | `human` o `UNCONFIRMED`; autoridad de esa política. |

La lectura, serialización, defaults y validez de los tres componentes se
derivan exclusivamente del
[contrato de configuración lifecycle](lifecycle-config-v1.md).

### Estado local

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 24 | `LOCAL` | `source-result` de la observación local. |
| 25 | `LOCAL_VERSIONING` | `GIT | NO_COMMIT | UNVERSIONED | UNKNOWN`. |
| 26 | `LOCAL_SOURCE` | `GIT_QUERY` para Git/No commit; `WORKSPACE_METADATA` en otro caso. |
| 27 | `LOCAL_EVIDENCE_LEVEL` | `evidence`; referencia: `VERIFIED_DIRECT`. |
| 28 | `LOCAL_FINGERPRINT_MODE` | `INDEX_CONTENT_BOUNDED | TREE_CONTENT_BOUNDED`. |
| 29 | `LOCAL_FINGERPRINT` | `hex64`; huella local final utilizable. |
| 30 | `LOCAL_FINGERPRINT_STARTED` | `hex64`; huella al abrir la ventana. |
| 31 | `LOCAL_FINGERPRINT_FINISHED` | `hex64` o `UNAVAILABLE`; sonda local final. |
| 32 | `LOCAL_CHANGED_DURING_CHECK` | `bool` derivado de las dos huellas de ventana. |
| 33 | `LOCAL_COMMIT` | OID Git observado o sentinel (`NO_COMMIT`, `NOT_APPLICABLE`, `UNKNOWN`). |
| 34 | `LOCAL_BRANCH` | Rama observada o sentinel explícito. |
| 35 | `LOCAL_DIRTY` | `bool`; diferencia conservadora de bytes/modo frente a índice/árbol. |
| 36 | `LOCAL_DIRTY_MODE` | Fijo `RAW_NO_FILTERS_CONSERVATIVE`. |
| 37 | `LOCAL_DIRTY_COUNT` | `count` de entradas distintas. |
| 38 | `LOCAL_ENTRY_COUNT` | `count` de entradas incluidas en la huella. |
| 39 | `LOCAL_SCAN_STATUS` | Código extensible; referencia: `COMPLETE` o causa de límite/fallo. |
| 40 | `LOCAL_GIT_SAFE_OVERRIDE` | `PER_COMMAND | NOT_REQUIRED`. |
| 41 | `LOCAL_OBSERVED_AT_UTC` | `utc`; instante de la observación local. |

La huella local usa contenido acotado y declara
`INDEX_CONTENT_BOUNDED` para `GIT`/`NO_COMMIT`; usa
`TREE_CONTENT_BOUNDED` para los demás valores. Alcanzar un límite obliga a
`LOCAL=PARTIAL`: la huella no se presenta como exhaustiva. En Git, calcular
dirty con índice/árbol y bytes crudos, sin ejecutar filtros ni atributos. Ambas
variantes usan el formato normativo `SEXTANTE_LOCAL_V4`, definido byte por byte
en el [contrato de huella local](local-fingerprint-v1.md); mtime no participa
en la identidad.

`LOCAL=ALIGNED` o `DRIFT` exige `LOCAL_SCAN_STATUS=COMPLETE`, evidencia
`VERIFIED_DIRECT` y una ventana local sin cambios. `LOCAL=PARTIAL` representa
una sonda incompleta o Git indeterminado; `LOCAL=STALE` exige que la ventana
haya cambiado. `LOCAL_SOURCE` se deriva de `LOCAL_VERSIONING`, no se declara
libremente.

### Integridad del adaptador y frontera

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 42 | `ADAPTER_FINGERPRINT_STARTED` | `hex64`; huella del adaptador al inicio. |
| 43 | `ADAPTER_FINGERPRINT_FINISHED` | `hex64` o `UNAVAILABLE`; sonda final. |
| 44 | `ADAPTER_FINAL_STATUS` | `COMPLETE | UNAVAILABLE`. |
| 45 | `ADAPTER_CHANGED_DURING_CHECK` | `bool` derivado de las huellas del adaptador. |
| 46 | `OBSERVATION_BOUNDARY` | Fijo `FINAL_PROBES_BEFORE_RECEIPT_PUBLICATION`. |

La ventana observada termina en las sondas finales, antes de publicar el
comprobante. Un cambio posterior pertenece a otra ejecución.

### Repositorio remoto

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 47 | `REMOTE` | `source-result` de la fuente remota. |
| 48 | `REMOTE_STATE` | Código extensible de resultado o impedimento remoto. |
| 49 | `REMOTE_NAME` | Nombre Git seleccionado o `NONE`. |
| 50 | `REMOTE_URL` | URL HTTP(S) exacta aprobable, o representación redactada/sentinel si se rechazó. |
| 51 | `REMOTE_COMMIT` | OID de `REMOTE_REF` o `UNKNOWN`/`NOT_APPLICABLE`; nunca HEAD inferido. |
| 52 | `REMOTE_REF` | Ref exacta `refs/heads/<rama-local>` o sentinel. |
| 53 | `REMOTE_SOURCE_ID` | `sha256:` seguido de 64 hex, `UNRESOLVED` o `NOT_APPLICABLE`; identidad exacta cuando existe. |
| 54 | `REMOTE_QUERY_CONFIRMED_SOURCE_ID` | `REMOTE_SOURCE_ID` aprobado o `UNCONFIRMED`. |
| 55 | `REMOTE_REDIRECT_POLICY` | Fijo `DENY` en v1. |
| 56 | `REMOTE_QUERY_ATTEMPTED` | `bool`; si se intentó la consulta de red. |
| 57 | `REMOTE_CANDIDATES` | Lista CSV de nombres remotos, vacía cuando no aplica. |
| 58 | `REMOTE_EVIDENCE_LEVEL` | `evidence`. |
| 59 | `REMOTE_QUERY_CONFIRMED_BY` | `human` que aprobó la fuente exacta o `UNCONFIRMED`. |
| 60 | `REMOTE_MAX_AGE_SECONDS` | `max-age`. |
| 61 | `REMOTE_OBSERVED_AT_UTC` | `utc`. |

Para una fuente consultable:

```text
REMOTE_SOURCE_ID =
  "sha256:" + sha256(
    "sextante-remote-source-v1" NUL
    WORKSPACE_PATH_RESUELTO NUL
    REMOTE_NAME NUL
    URL_DE_CONSULTA_EXACTA NUL
    REMOTE_REF NUL
    REMOTE_REDIRECT_POLICY
  )
```

No intentar red hasta que `REMOTE_QUERY_CONFIRMED_BY` sea `human` y
`REMOTE_QUERY_CONFIRMED_SOURCE_ID == REMOTE_SOURCE_ID`. La aprobación queda
atada al workspace, nombre, URL, ref y política de redirección; no confirma
`TARGET`, push ni deploy. Consultar solo la ref exacta y con redirects
deshabilitados.

Estados v1 con reglas especiales:

- `NETWORK_CONFIRMATION_REQUIRED`: ambos campos de confirmación son
  `UNCONFIRMED` y `REMOTE_QUERY_ATTEMPTED=FALSE`.
- `SOURCE_CONFIRMATION_MISMATCH`: existe actor humano, el ID aprobado difiere
  del actual y no se intentó red.
- `VERIFIED`: se intentó la consulta con actor humano e IDs iguales.

`REMOTE=ALIGNED` o `DRIFT` exige estado `VERIFIED`, evidencia
`VERIFIED_DIRECT`, OID de 40 o 64 hex, ref concreta y fuente resuelta. El
validador vuelve a clasificar la URL y recalcula `REMOTE_SOURCE_ID` desde los
cinco valores normativos. `REMOTE=NOT_APPLICABLE` solo corresponde a `NO_GIT`
o `NO_REMOTE`, sin consulta y con ref/source-id `NOT_APPLICABLE`.
`REMOTE=STALE` usa `EVIDENCE_EXPIRED`; una ausencia esperada por State Map se
degrada a `PARTIAL`, nunca se convierte artificialmente en `DRIFT`.

### Runtime

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 62 | `RUNTIME` | `source-result`. |
| 63 | `RUNTIME_STATE` | Código extensible del estado de la observación. |
| 64 | `RUNTIME_VERSION` | Versión observada o sentinel. |
| 65 | `RUNTIME_TARGET` | Destino runtime observado y no ambiguo, o `UNKNOWN`/`NOT_APPLICABLE`. |
| 66 | `RUNTIME_SOURCE` | Fuente concreta de la evidencia o `NOT_PROVIDED`. |
| 67 | `RUNTIME_CANDIDATES` | Lista CSV de candidatos. |
| 68 | `RUNTIME_MAX_AGE_SECONDS` | `max-age`. |
| 69 | `RUNTIME_EVIDENCE_LEVEL` | `evidence`. |
| 70 | `RUNTIME_OBSERVED_AT_UTC` | `utc`. |

`RUNTIME=ALIGNED` o `DRIFT` requiere fuente concreta, evidencia fuerte
(`VERIFIED_DIRECT` o `HUMAN_PROVIDED`), `RUNTIME_STATE=VERIFIED` y
`RUNTIME_TARGET` explícito. Si falta el destino, usar `RUNTIME=PARTIAL` y
`RUNTIME_STATE=TARGET_MISSING`; no elegirlo por inferencia.
`RUNTIME=NOT_APPLICABLE` también exige fuente concreta y evidencia fuerte.
`RUNTIME=STALE` se deriva por vigencia y usa `EVIDENCE_EXPIRED`; no se acepta
como afirmación manual literal.

Una declaración de proyecto `RUNTIME_MODE=NONE` sin esa corroboración produce
`RUNTIME=PARTIAL`, `RUNTIME_STATE=EVIDENCE_UNVERIFIED`,
`RUNTIME_SOURCE=SOURCES.env` y `RUNTIME_EVIDENCE_LEVEL=DECLARED`; nunca
habilita deploy.

### Capacidades del harness

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 71 | `CAPABILITIES` | `source-result`. |
| 72 | `CAPABILITIES_STATE` | Código extensible del inventario. |
| 73 | `CAPABILITIES_HASH` | `hex64`; hash de las entradas normalizadas. |
| 74 | `CAPABILITIES_SOURCE` | `HUMAN_INPUT | HARNESS_CONTEXT | NOT_PROVIDED`. |
| 75 | `CAPABILITY_COUNT` | Entero 0..999; número exacto de entradas dinámicas. |
| 76 | `CAPABILITIES_MAX_AGE_SECONDS` | `max-age`. |
| 77 | `CAPABILITIES_EVIDENCE_LEVEL` | `evidence`. |
| 78 | `CAPABILITIES_OBSERVED_AT_UTC` | `utc`. |

Después de `DECIDED_BY`, emitir exactamente las claves consecutivas
`CAPABILITY_001` a `CAPABILITY_<CAPABILITY_COUNT con tres dígitos>`. Cada valor
usa:

```text
KIND|NAME|STATE|VERSION
```

`KIND` y `NAME` no son vacíos; `STATE` es
`DETECTED | LOADED | INVOKABLE | UNAVAILABLE | UNKNOWN`; `VERSION` puede ser
`UNKNOWN`. El productor de referencia elimina duplicados y ordena las entradas.
Calcular:

```text
CAPABILITIES_HASH = sha256(UTF8(entry_001 + "\n" + ... + entry_NNN))
```

Sin entradas, el material es la cadena vacía. `CAPABILITIES=ALIGNED` exige
entradas, ninguna capacidad `UNKNOWN` y evidencia fuerte:
`VERIFIED_DIRECT` o `HUMAN_PROVIDED`. `DECLARED` y `UNKNOWN` nunca alinean.
La relación exacta es:

```text
sin entradas                         -> PARTIAL / NOT_PROVIDED
alguna entrada con state UNKNOWN     -> PARTIAL / INCOMPLETE
inventario con evidencia débil       -> PARTIAL / EVIDENCE_UNVERIFIED
inventario completo y evidencia fuerte -> ALIGNED / INVENTORIED
```

Solo un inventario base completo puede pasar a `DRIFT` por State Map o a
`STALE/EVIDENCE_EXPIRED` por vigencia. `CAPABILITIES=NOT_APPLICABLE` no existe
en v1.

### Veredicto, gates, target y autoría

| # | Campo | Forma y significado |
| ---: | --- | --- |
| 79 | `STATE_VERDICT` | `ALIGNED | DRIFT | PARTIAL | STALE`. |
| 80 | `READ_GATE` | `PASS | WARN`. |
| 81 | `WRITE_GATE` | `PASS | BLOCK`. |
| 82 | `TARGET` | `UNCONFIRMED | CONFIRMED`. |
| 83 | `TARGET_WHERE` | Destino exacto confirmado o `UNCONFIRMED`. |
| 84 | `TARGET_ACTION` | `UNCONFIRMED | EDIT | PUSH | DEPLOY`. |
| 85 | `TARGET_CONFIRMED_BY` | `human` o `UNCONFIRMED`. |
| 86 | `HUMAN_DECISION` | `NONE | CONFIRM_TARGET | CHOOSE_SOURCE | PROVIDE_ACCESS | CONFIRM_SOURCE_ACCESS | ACCEPT_RISK | STOP`. |
| 87 | `DECISION_REASON` | Código de razón o `NONE`. |
| 88 | `COLLECTED_BY` | `actor` que obtuvo la evidencia. |
| 89 | `SYNTHESIZED_BY` | `mother-session`; dueña del criterio final. |
| 90 | `DECIDED_BY` | `human` responsable de decisión/target o `NONE`. |
| 91 | `RECEIPT_HASH` | `hex64`; integridad canónica y última línea física. |

## Relaciones semánticas obligatorias

### Configuración y autoridad

- Validar lifecycle y sus componentes mediante el
  [contrato portable de configuración](lifecycle-config-v1.md).
- `LIFECYCLE=NOT_ADOPTED` exige los tres componentes `ABSENT`;
  `LIFECYCLE=INVALID` exige los tres `INVALID`.
- `CONFIG_STATUS=INVALID` si y solo si alguno de `POLICY_STATUS`,
  `SOURCES_STATUS` o `STATE_MAP_STATUS` es `INVALID`; en otro caso es `VALID`.
- Un archivo del proyecto no puede elevar la confianza de su README.
  `DISCOVERY_ONLY` y `DECLARED_TRUST` requieren
  `README_POLICY_SOURCE=SESSION_HUMAN` y
  `README_POLICY_CONFIRMED_BY=human:...`.
- `COLLECTED_BY` puede identificar sesión, agente, humano o harness.
  `SYNTHESIZED_BY` siempre identifica la sesión madre.

### Corroboración contra State Map

- Validar primero el [esquema portable de State Map](state-map-v1.md).
- Si `GIT_LOCAL_FINGERPRINT` es conocido, prevalece y se compara con
  `LOCAL_FINGERPRINT`; no se produce un segundo veredicto por
  `GIT_LOCAL_COMMIT`.
- Solo si falta una huella local conocida, `GIT_LOCAL_COMMIT` conocido funciona
  como base/fallback frente a `LOCAL_COMMIT`. Un State Map versionado no puede
  contener de forma estable el OID del mismo commit que lo crea, porque ese
  contenido cambiaría el OID; por eso el commit representa la base observada y
  la huella normalizada es el ancla preferida.
- Un `GIT_REMOTE_COMMIT` concreto requiere un `GIT_REMOTE_REF` conocido. La
  corroboración compara primero la ref y luego el OID de esa misma ref; nunca
  sustituye la ref por HEAD.

### Trazas de cambio

- `LOCAL_CHANGED_DURING_CHECK=TRUE` si la sonda final es `UNAVAILABLE` o si
  cambió huella, commit o rama durante la ventana. El recibo conserva solo
  commit/rama finales, por lo que el validador puede recomputar la diferencia
  de huellas y debe aceptar un `TRUE` adicional producido por cambio exclusivo
  de commit/rama. Si la huella final está disponible,
  `LOCAL_FINGERPRINT == LOCAL_FINGERPRINT_FINISHED`.
- `ADAPTER_CHANGED_DURING_CHECK=TRUE` si la huella final del adaptador es
  `UNAVAILABLE` o difiere de la inicial.
- `ADAPTER_FINAL_STATUS=COMPLETE` si y solo si la huella final es `hex64`;
  en otro caso es `UNAVAILABLE`.
- Una diferencia entre `SKILL_VERSION` y `SKILL_VERSION_FINISHED` también
  vuelve stale la ejecución.

### Vigencia

Para `REMOTE`, `RUNTIME` y `CAPABILITIES`, calcular:

```text
age = FINISHED_AT_UTC - <FUENTE>_OBSERVED_AT_UTC
```

Si el resultado es `ALIGNED`, `DRIFT` o `NOT_APPLICABLE`, debe cumplirse
`-300 <= age <= <FUENTE>_MAX_AGE_SECONDS`. Fuera de esa ventana usar
`STALE/EVIDENCE_EXPIRED`. No se puede usar `STALE/EVIDENCE_EXPIRED` mientras la
edad siga dentro de la ventana.

### Veredicto y gates

Derivar `STATE_VERDICT` en esta precedencia:

1. `STALE` si cambió local/adaptador/versión o alguna fuente vale `STALE`.
2. `DRIFT` si alguna fuente vale `DRIFT`.
3. `PARTIAL` si alguna fuente vale `PARTIAL`, la configuración es inválida, o
   el lifecycle está adoptado sin `STATE_MAP_STATUS=LOADED`.
4. `ALIGNED` en cualquier otro caso.

`READ_GATE=PASS` solo para `STATE_VERDICT=ALIGNED`; de lo contrario es `WARN`.

Para `WRITE_GATE=PASS` deben cumplirse primero todas estas condiciones:

- `INTENT != read` y `STATE_VERDICT != STALE`;
- `CONFIG_STATUS=VALID`;
- baseline listo: `LIFECYCLE=NOT_ADOPTED`, o bien
  `LIFECYCLE=ADOPTED` con `STATE_MAP_STATUS=LOADED`;
- `TARGET=CONFIRMED`, `TARGET_ACTION == upper(INTENT)` y target exacto;
- `LOCAL=ALIGNED` y `CAPABILITIES=ALIGNED`.

El target exacto se deriva sin elección del modelo:

```text
edit   -> local:workspace
push   -> remote:<REMOTE_NAME>:<REMOTE_REF>
deploy -> RUNTIME_TARGET
read   -> UNCONFIRMED
```

Un dato requerido ausente produce `UNAVAILABLE` y bloquea. Cumplida la base:

- `edit` pasa;
- `push` pasa solo con `REMOTE=ALIGNED`;
- `deploy` pasa solo con `REMOTE=ALIGNED|NOT_APPLICABLE` y
  `RUNTIME=ALIGNED`;
- cualquier otro caso bloquea.

`TARGET=UNCONFIRMED` exige el triple
`TARGET_WHERE/TARGET_ACTION/TARGET_CONFIRMED_BY=UNCONFIRMED`.
`TARGET=CONFIRMED` exige destino no vacío, acción de escritura y actor humano.
Con `INTENT=read` el target siempre queda sin confirmar. Si hay target
confirmado, `DECIDED_BY == TARGET_CONFIRMED_BY`; otro `DECIDED_BY` distinto de
`NONE` también debe ser humano.

`HUMAN_DECISION=NONE` si y solo si `DECISION_REASON=NONE`. Una decisión
pendiente usa un valor distinto de `NONE` en ambos campos.

## Integridad y almacenamiento

El hash detecta alteraciones, pero no autentica al autor: quien pueda reemplazar
todo el archivo también puede recalcularlo. Validar estructura/hash tampoco
vuelve vigente la evidencia; siempre aplicar timestamps, trazas y gates.

Crear el comprobante de forma atómica y sin sobrescritura; una colisión de
nombre falla. Escribir dentro de `.lifecycle/local/sextante/` únicamente si:

- `.lifecycle/` ya existe y no es enlace/junction;
- `.lifecycle/.gitignore` es un archivo regular y estable, y `local/` es su
  última regla activa: la última línea no vacía y no comentada debe ser
  exactamente `local/`;
- la ruta local y el destino no son enlaces/junctions.

En cualquier otro caso usar almacenamiento local del harness fuera del
workspace. Sextante no crea ni modifica el ignore durante una consulta.

## Salida visible

Emitir exactamente estas nueve líneas, en orden:

```text
LOCAL=...
REMOTE=...
RUNTIME=...
CAPABILITIES=...
STATE_VERDICT=...
READ_GATE=...
WRITE_GATE=...
TARGET=...
RECEIPT=...
```

Agregar solo cuando corresponda:

```text
HUMAN_DECISION=...
DECISION_REASON=...
```

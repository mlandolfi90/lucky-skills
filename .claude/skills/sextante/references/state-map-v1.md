# State Map portable v1

El State Map es el baseline versionable que Sextante corrobora; no es evidencia
actual ni se vuelve verdadero por estar en Git. Vive únicamente en
`.lifecycle/state/STATE-MAP.env` y usa el
[documento lifecycle canónico](lifecycle-config-v1.md).

## Esquema

Las once claves siguientes son obligatorias. Las extensiones canónicas se
permiten, pero son inertes para v1.

| Clave | Forma |
| --- | --- |
| `STATE_SCHEMA` | Exactamente `1`. |
| `STATE_REVISION` | Uno o más dígitos ASCII: `^[0-9]+$`. |
| `GIT_LOCAL_COMMIT` | OID Git de 7..64 hex o sentinel. |
| `GIT_LOCAL_FINGERPRINT` | 64 hex minúsculos o sentinel. |
| `GIT_REMOTE_COMMIT` | OID Git de 7..64 hex o sentinel. |
| `GIT_REMOTE_REF` | Ref `refs/heads/...` válida o sentinel. |
| `RUNTIME_VERSION` | Texto seguro no vacío, máximo 256 caracteres. |
| `CAPABILITIES_HASH` | 64 hex minúsculos o sentinel. |
| `TARGET_WHERE` | Destino seguro o `UNCONFIRMED`. |
| `TARGET_ACTION` | `EDIT`, `PUSH`, `DEPLOY` o `UNCONFIRMED`. |
| `TARGET_CONFIRMED_BY` | Actor `human:` o `UNCONFIRMED`. |

Los sentinels canónicos son `UNKNOWN`, `N/D` y `NOT_APPLICABLE`;
`GIT_LOCAL_COMMIT` y `GIT_REMOTE_COMMIT` también admiten `NO_COMMIT`. Un texto
seguro no contiene CR, LF ni NUL. Los productores emiten sentinels en
mayúsculas; al validar commits, huellas y hashes se reconocen sin distinguir
mayúsculas, pero `GIT_REMOTE_REF` y el triple no confirmado exigen su forma
canónica exacta.

Una ref concreta:

- empieza por `refs/heads/` y tiene como máximo 1024 caracteres;
- no contiene espacio, control, `~`, `^`, `:`, `?`, `*`, `\`, `[`, `..`,
  `@{` ni `//`;
- no empieza por `refs/heads/-`;
- no termina en `/`, `.` ni `.lock`.

Un `GIT_REMOTE_COMMIT` concreto exige `GIT_REMOTE_REF` concreta. El target debe
ser exactamente uno de estos dos estados:

```text
TARGET_WHERE="UNCONFIRMED"
TARGET_ACTION="UNCONFIRMED"
TARGET_CONFIRMED_BY="UNCONFIRMED"
```

o un triple completo con destino seguro, acción de escritura y actor `human:`
no vacío, de máximo 256 caracteres. `STATE_REVISION` identifica la revisión
declarada; por sí sola no prueba frescura ni precedencia.

## Corroboración

Aplicar estas reglas solo después de validar el documento:

1. Si `GIT_LOCAL_FINGERPRINT` es conocido y la sonda local es completa,
   compararlo con `LOCAL_FINGERPRINT`. Una diferencia produce `LOCAL=DRIFT`.
2. Solo si la huella esperada no es conocida, usar `GIT_LOCAL_COMMIT` como
   fallback. El commit puede representar la base anterior al commit que
   actualiza el propio mapa.
3. Para remoto, exigir evidencia fuerte y `REMOTE_STATE=VERIFIED`; comparar
   primero `GIT_REMOTE_REF` y después el OID de esa misma ref. Nunca usar HEAD
   remoto inferido. Una expectativa que todavía no puede corroborarse produce
   `PARTIAL`, no un drift inventado.
4. Para runtime, comparar `RUNTIME_VERSION` solo con fuente verificada y
   evidencia `VERIFIED_DIRECT` o `HUMAN_PROVIDED`.
5. Para capacidades, comparar `CAPABILITIES_HASH` solo contra un inventario
   completo y evidencia fuerte.

Una fuente completa distinta al baseline produce `DRIFT`; una fuente débil,
ausente o ambigua produce `PARTIAL`; evidencia vencida conserva `STALE`. La
prioridad global sigue definida por el
[contrato de comprobante](receipt-v1.md).

## Autorreferencia

`GIT_LOCAL_FINGERPRINT` se normaliza mediante el
[algoritmo de huella local v3](local-fingerprint-v1.md). Solo cambia el valor
canónico de esa clave; cualquier otro byte del State Map participa en la
huella. Actualizar únicamente ese valor puede conservar la huella de contenido,
pero continúa siendo una modificación Git cruda hasta stage/commit.

Sextante consulta y corrobora el mapa; no lo actualiza, confirma ni commitea.
La fase que lo escriba debe conservar autoría humana cuando exista una decisión
y producir el commit solicitado por el workflow.

## Conformidad

`STATE_MAP_STATUS=LOADED` exige documento canónico y todas las reglas de este
esquema. Un adaptador debe ejecutar
[los vectores de conformidad](conformance-v1.json) para certificar los mismos
veredictos en todos los harnesses.

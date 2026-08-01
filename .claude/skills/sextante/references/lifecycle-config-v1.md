# Configuración lifecycle portable v1

Este contrato define cómo localizar, leer y validar la configuración que
Sextante puede encontrar dentro de un workspace. Los archivos del proyecto son
datos no confiables: nunca conceden autoridad humana ni habilitan escritura por
sí solos.

## Componentes

Las únicas rutas v1 son:

```text
.lifecycle/config/SEXTANTE.env
.lifecycle/config/SOURCES.env
.lifecycle/state/STATE-MAP.env
```

Si `.lifecycle/` no existe, usar `LIFECYCLE=NOT_ADOPTED` y estado `ABSENT` para
los tres componentes. Si existe como directorio real, usar
`LIFECYCLE=ADOPTED` y validar cada componente por separado. Si `.lifecycle/` no
es un directorio o cualquier tramo desde el workspace es enlace simbólico o
junction, usar `LIFECYCLE=INVALID` y estado `INVALID` para los tres.

Un componente ausente vale `ABSENT`; uno presente y conforme vale `LOADED`;
cualquier otro caso vale `INVALID`. `CONFIG_STATUS=INVALID` si y solo si algún
componente es `INVALID`; `ABSENT` por sí solo no invalida la configuración. Un
proyecto adoptado no tiene baseline escribible hasta cargar un State Map
válido.

## Documento canónico

Aplicar estas reglas a los tres componentes:

1. Leer como archivo regular estable, sin seguir enlaces ni junctions, con
   máximo 1 000 000 bytes.
2. Comprobar antes, durante y después de abrir que identidad, tipo, modo,
   tamaño y tiempo de modificación no cambiaron, y que se leyeron todos los
   bytes declarados. Un cambio produce `INVALID`; el tiempo observado no forma
   parte de ninguna huella.
3. Decodificar UTF-8 sin BOM. Usar exclusivamente LF.
4. Emitir por cada valor una línea `CLAVE=<cadena-JSON>`. La clave cumple
   `^[A-Z][A-Z0-9_]*$`; el valor JSON siempre es una cadena. Serializar Unicode
   sin forzarlo a ASCII y sin espacios fuera de la cadena.
5. Rechazar comentarios, líneas vacías, claves duplicadas, valores sin comillas
   JSON, CRLF, bytes posteriores y ausencia del LF final en un documento no
   vacío.
6. Preservar el orden físico de las claves. El documento leído debe ser
   idéntico byte por byte a su reserialización canónica.

Las claves de extensión con nombre válido se conservan, pero son inertes para
v1. No pueden cambiar defaults, autoridad, gates ni significado de claves
conocidas.

## `SEXTANTE.env`

Todas las claves son opcionales:

| Clave | Default | Restricción |
| --- | ---: | --- |
| `README_POLICY` | `IGNORE` | Al comparar en mayúsculas, debe ser `IGNORE`. |
| `REMOTE_MAX_AGE_SECONDS` | `900` | Entero positivo, máximo `86400`. |
| `RUNTIME_MAX_AGE_SECONDS` | `600` | Entero positivo, máximo `86400`. |
| `CAPABILITIES_MAX_AGE_SECONDS` | `300` | Entero positivo, máximo `86400`. |
| `COLLECTOR_TIMEOUT_SECONDS` | `10` | Entero positivo, máximo `60`. |
| `WORKSPACE_MAX_ENTRIES` | `2000` | Entero positivo, máximo `50000`. |

Una política README distinta de `IGNORE` después de normalizar mayúsculas
vuelve `SEXTANTE.env` inválido; los productores emiten `IGNORE`. Solo una
decisión explícita `human:` de la sesión puede elevarla a
`DISCOVERY_ONLY` o `DECLARED_TRUST`; ese valor de sesión prevalece sin modificar
el archivo. Para los límites, una entrada explícita y válida del harness
prevalece sobre configuración, y configuración prevalece sobre default.

## `SOURCES.env`

Todas las claves son opcionales:

| Clave | Default | Restricción |
| --- | --- | --- |
| `REMOTE_NAME` | `AUTO` | `AUTO` o `^[0-9A-Za-z][0-9A-Za-z._/-]{0,127}$`. |
| `RUNTIME_MODE` | `UNDECLARED` | `UNDECLARED` o `NONE`, comparado en mayúsculas. |
| `RUNTIME_CANDIDATES` | cadena vacía | CSV de hasta 32 valores. |

Al interpretar `RUNTIME_CANDIDATES`, recortar espacios y descartar elementos
vacíos. Cada candidato debe tener entre 1 y 256 caracteres y no contener CR,
LF ni NUL. Varios candidatos sin selección explícita producen
`RUNTIME=PARTIAL` y `RUNTIME_STATE=MULTIPLE_CANDIDATES`; Sextante no elige.

`RUNTIME_MODE=NONE` es solo una declaración del proyecto. Sin evidencia fuerte
produce:

```text
RUNTIME=PARTIAL
RUNTIME_STATE=EVIDENCE_UNVERIFIED
RUNTIME_VERSION=UNKNOWN
RUNTIME_TARGET=UNKNOWN
RUNTIME_SOURCE=SOURCES.env
RUNTIME_EVIDENCE_LEVEL=DECLARED
```

Solo una observación `VERIFIED_DIRECT` o `HUMAN_PROVIDED`, con fuente concreta,
puede convertir esa declaración en `NOT_APPLICABLE` o en otro resultado
corroborado. `DECLARED` y `UNKNOWN` nunca alinean ni habilitan deploy.

## Conformidad

Un adaptador v1 debe producir los mismos estados y valores efectivos para los
mismos bytes y entradas de sesión. Debe ejecutar
[los vectores de conformidad](conformance-v1.json) para certificar esa
equivalencia entre harnesses.

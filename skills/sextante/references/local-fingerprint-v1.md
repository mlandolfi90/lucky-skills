# Huella local portable v5

Este documento fija el algoritmo de `LOCAL_FINGERPRINT` para
`CONTRACT_VERSION=1`. La huella identifica contenido: rutas y contenido
canónico dentro de una ventana acotada. La posición en git — commit, rama,
índice —, los modos, la suciedad y la vigencia se registran y verifican aparte;
incluirlos en la huella hacía que adoptar en una rama y mergear a otra
produjera drift permanente sin que cambiara un byte, y que Windows y Linux
divergieran por el bit ejecutable.

**Contenido canónico (v5).** El material que se hashea son los bytes con CRLF
convertido a LF, salvo que el contenido sea binario — NUL en los primeros 8000
bytes, el mismo criterio de git. Antes se hasheaban los bytes del checkout, y
con `core.autocrlf` git los reescribe al bajar los archivos: el mismo commit
producía huellas distintas según la máquina y según qué herramienta escribió
cada archivo. Un clon nunca reproducía la huella sellada y `revalidar` no
convergía jamás; y el STATE-MAP, que se versiona y viaja a cada destino,
llevaba adentro un valor que sólo valía para un checkout. Git guarda LF, así
que normalizar devuelve el contenido versionado. El tamaño del registro es el
del contenido canónico, nunca el del archivo en disco: si el registro delatara
la conversión, dos checkouts del mismo commit volverían a divergir con el mismo
digest. Los OID crudos siguen disponibles aparte, y contra el índice de git se
compara el canónico — un archivo intacto en CRLF salía sucio con el árbol
limpio.

Migración: toda huella sellada antes de v5 queda inválida. Cada repositorio
adoptado revalida una vez; el salto queda en su recibo.

## Codificación común

El identificador de formato es `SEXTANTE_LOCAL_V4`. Cada registro es un array
JSON cuyos elementos son cadenas:

1. Convertir cada campo a texto sin normalización Unicode.
2. Serializar el array con ASCII obligatorio, escapes JSON, sin espacios y con
   separadores exactos `,` y `:`; equivale a
   `ensure_ascii=true, separators=(",", ":")`.
3. Unir los registros, en su orden normativo, con un byte LF. No agregar LF
   final.
4. Calcular SHA-256 sobre esos bytes ASCII y emitir 64 hex minúsculos.

Ejemplo de registro:

```json
["ENTRY","src/main.py","FILE","12","CANONICAL","<sha256>"]
```

Usar escapes `\uXXXX` con hex minúsculos y pares surrogate para puntos mayores
que U+FFFF; no escapar `/`. Representar todo path relativo con `/`, sin cambiar
case ni normalizar Unicode.

Ordenar paths únicos por secuencia ascendente de puntos de código Unicode.
Un path o rama que contenga U+FFFD o un surrogate U+D800..U+DFFF no es
portable: degradar a `LOCAL=PARTIAL` con causa `UNSUPPORTED_PATH_TEXT` o, si se
detecta dentro de un snapshot Git inválido, `GIT_SNAPSHOT_INVALID`.

## Lectura de entradas

Aplicar `WORKSPACE_MAX_ENTRIES`, `COLLECTOR_TIMEOUT_SECONDS` y un máximo total
de 512 MiB de contenido; leer archivos en bloques de hasta 1 MiB. Para cada
archivo regular, comparar identidad, tipo, modo, tamaño y mtime antes, durante
y después de abrir. El mtime sirve únicamente para detectar carreras: nunca
entra en un registro ni en la huella.

Los registros de entrada son:

```text
["ENTRY","UNSUPPORTED_PATH_TEXT"]
["ENTRY",path,"UNSAFE_PATH"]
["ENTRY",path,"MISSING"]
["ENTRY",path,"SYMLINK",sha256_destino]
["ENTRY",path,"SPECIAL",bits_de_tipo]
["ENTRY",path,"CONTENT_LIMIT",tamaño]
["ENTRY",path,causa_de_fallo,tamaño]
["ENTRY",path,"FILE",tamaño_canónico,"CANONICAL",sha256_contenido_canónico]
["ENTRY",path,"FILE",tamaño_normalizado,"NORMALIZED_SELF_VALUE",sha256_bytes_normalizados]
```

Todos los números se convierten a cadenas JSON. `sha256_destino` usa los bytes
UTF-8 del texto del destino del enlace; el archivo enlazado no se sigue. Un
path absoluto, con drive o con componente `..` es inseguro. Un límite, entrada
especial, cambio durante lectura, texto no portable o fallo de lectura vuelve
incompleta la sonda y obliga `LOCAL=PARTIAL`.

El modo del archivo no participa en ningún registro: el mismo árbol produce la
misma huella esté trackeado o no, en Windows o en Linux. El bit POSIX
observable se verifica por separado en la detección de dirty, donde el sistema
lo expone.

## Variante Git: `INDEX_CONTENT_BOUNDED`

Consultar sin mutar:

```text
git rev-parse --verify HEAD
git symbolic-ref --quiet --short HEAD
git ls-files --stage -z --cached
git ls-files -z --others --exclude-standard
git rev-parse --show-object-format
git ls-tree -r -z HEAD
```

Omitir el último comando cuando no exista commit. No ejecutar filtros,
atributos, hooks, fetch ni escritura. El formato de objetos debe ser `sha1` o
`sha256`.

Formar los registros en este orden:

```text
["FORMAT","SEXTANTE_LOCAL_V4"]
["VERSIONING","GIT"]
<registros ENTRY por path ordenado>
```

Para contenido, usar la unión única de paths trackeados que no sean submódulos
y paths untracked devueltos por Git. Rama, índice, árbol de HEAD y formato de
objetos no entran en la huella: son posición, no contenido. El commit se
conserva separadamente como `LOCAL_COMMIT`, la rama como observación propia, y
el índice y los OID alimentan solo la detección de dirty.

Si no puede construirse el snapshot Git, producir una huella parcial con:

```text
["FORMAT","SEXTANTE_LOCAL_V4"]
["VERSIONING","GIT"]
["SCAN_STATUS",causa]
```

## Variante sin Git: `TREE_CONTENT_BOUNDED`

Recorrer el workspace de arriba abajo, sin seguir enlaces de directorio y
ordenando nombres en cada nivel. Registrar el enlace como entrada. Excluir el
path relativo a la raíz exacto y cualquier descendiente de:

```text
.git
.hg
.svn
.lifecycle/local
__pycache__
.pytest_cache
.mypy_cache
.venv
venv
node_modules
dist
build
coverage
```

Formar:

```text
["FORMAT","SEXTANTE_LOCAL_V4"]
["VERSIONING","UNVERSIONED|UNKNOWN"]
<registros ENTRY por path ordenado>
```

Usar `UNKNOWN` y forzar `PARTIAL` si Git no está disponible o su detección no
es concluyente; usar `UNVERSIONED` solo cuando se corroboró que no es un repo.

## Normalización autorreferencial

Solo para `.lifecycle/state/STATE-MAP.env`, con máximo 1 000 000 bytes:

1. Separar líneas conservando exactamente su terminador.
2. Exigir una sola línea cuyo cuerpo empiece por
   `GIT_LOCAL_FINGERPRINT="`, termine en `"` y no contenga otra comilla ni NUL
   dentro del valor.
3. Reemplazar únicamente ese cuerpo por
   `GIT_LOCAL_FINGERPRINT="<EXCLUDED_SELF_VALUE>"`; preservar el terminador y
   todos los demás bytes.
4. Usar tamaño y SHA-256 de los bytes normalizados en el registro `ENTRY`.

Cambiar el valor autorreferencial no cambia la huella; cambiar cualquier otro
byte sí.

## Dirty y conformidad

`LOCAL_DIRTY` no reutiliza la exclusión autorreferencial: comparar de forma
conservadora untracked, stages no cero, índice contra HEAD y modo POSIX
observable. Por eso un cambio solo en `GIT_LOCAL_FINGERPRINT` puede conservar
la huella y seguir dirty.

Contra el índice se compara el OID del contenido **canónico**, no el de los
bytes del disco: git guarda el contenido normalizado, así que con
`core.autocrlf` un archivo intacto en CRLF daba un OID crudo distinto al del
índice y salía sucio con `git status` limpio. La exclusión autorreferencial no
entra en esa comparación — el índice tiene el contenido real, y aplicársela
dejaría el STATE-MAP sucio para siempre.

Un adaptador debe ejecutar
[los vectores de conformidad](conformance-v1.json) antes de declararse
compatible. Los vectores fijan framing, hashes, configuración y
autorreferencia; las pruebas de integración cubren ambas variantes, límites y
modos.

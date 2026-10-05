# auditar-mcp · sugerencias desde Lucky-SecondBrian

| | |
|---|---|
| Quién la deja | la sesión de Claudian (seconbrian-cb) que construye Lucky-SecondBrian, por pedido de la operadora |
| Proyecto | `C:\Users\Vikingo\Desktop\Proyecto Afinamiento 1\Lucky-SecondBrian`, commit `e25a71b`: servidor MCP por stdio, TypeScript con el SDK oficial (`@modelcontextprotocol/sdk` 1.30.1), sólo lectura sobre una bóveda de Obsidian |
| Skill | `auditar-mcp` 1.6.4, publicada en `92e8686` y leída en `0d2dc35`, que sólo difiere en `manifest.env` (`skills/auditar-mcp/SKILL.md`) · paquete `lucky-auditoria-mcp` 0.9.0 |
| Estado del envío | **segunda entrega, abierta** (abajo, S-09 a S-31, desde el commit `b840538`). **Primera entrega:** Salió de leer la receta contra la auditoría ya construida (corte 6d, `docs/decisions/0007-auditoria-y-retencion.md` del proyecto). La receta se está aplicando ahora (incremento 7 del proyecto). Lo que se mida al aplicarla llega en una segunda entrega (R12), con su commit |

Contexto: la auditoría de este proyecto se diseñó a medida en el corte 6d, sin la receta. Al
preparar la entrega apareció el hueco, y la operadora decidió «adaptar para aplicar el metodo
pero si algo del metodo esta mal avisame para dejarle las mejoras a lucky skill en un buzon de
sugerencias» (2026-10-04). Lo que sigue es lo que la receta no cubre para este caso.

## S-01 · El «mismo JSONL» no tiene una especificación fuera del código Python

- **La receta:** R5 (`SKILL.md:538`) deja «Node · SDK TypeScript: pendiente, paquete hermano,
  mismo JSONL». R3 y R3-bis (`:493`, `:499`) listan los campos en prosa.
- **Este caso:** para escribir un hermano en TypeScript, la única fuente exacta es
  `src/lucky_auditoria/registro.py`. Los nombres, los tipos, cuál es obligatorio y cómo es la
  cabecera se reconstruyen leyendo Python.
- **Propuesta:** publicar en el paquete un esquema de la línea y de la cabecera (JSON Schema,
  versionado con el campo de versión de la cabecera) y un juego de líneas de ejemplo que los
  lectores de R9 acepten. Un hermano se valida contra eso, no contra el código del otro. Este
  proyecto va a ser la primera medición de la casilla de R5 (R6).

## S-02 · R1 no nombra el caso en que el proyecto es lo que el MCP sirve

- **La receta:** R1 (`:413`): todo va a `<CLAUDE_PROJECT_DIR>/registro_auditoria/`.
- **Este caso:** el MCP sirve una bóveda de Obsidian, y las sesiones que lo usan se abren en
  esa misma bóveda. `CLAUDE_PROJECT_DIR` es la bóveda, y su dueña decidió que el servidor no
  escribe en ella (plano del proyecto, §1). R1 por omisión pone la auditoría adentro de lo que
  el servidor tiene prohibido tocar.
- **Propuesta:** nombrar el caso «el proyecto es el backend» y mandarlo a la ruta absoluta de
  R4, o que el paquete se niegue a escribir dentro de lo que el MCP sirve y lo diga.

## S-03 · La cabecera al primer uso no deja lugar a un evento de arranque que hay que auditar

- **La receta:** R3-bis (`:499`) y la regla 6 (`:217`): la cabecera se escribe con la primera
  llamada; «un servidor que nadie usó no deja rastro».
- **Este caso:** el servidor lee un secreto por alias al arrancar (perfil MCP, F07), y esa
  lectura se audita: qué alias se leyó y si anduvo. Si falla, el servidor no arranca y no hay
  primera llamada: con la receta, la falla no queda en ningún registro.
- **Propuesta:** una línea de arranque sólo cuando hay un evento auditable antes de la primera
  llamada (por ejemplo, la lectura de un secreto), o la cabecera escrita en ese momento.

## S-04 · Retención automática: hay una medida

- **La receta:** R7 (`:567`): «Hoy nada limpia solo… la retención automática se declara
  pendiente hasta que alguien la mida en operación».
- **Este caso:** la retención es automática desde el corte 6d: N días (90 por omisión, clave
  `LUCKY_SB_AUDITORIA_DIAS`), al arrancar y con la primera escritura de cada día. Borra sólo los
  archivos con nombre de fecha. La E2E siembra archivos de 91 y 89 días y borra sólo el de 91.
  Sin la retención, 4 tests fallan.
- **Propuesta:** tomarla como medición (ficha, R6) y evaluar la retención por edad en el
  paquete.

## S-05 · R8 supone que el MCP ya tiene una herramienta de estado

- **La receta:** la regla 7 (`:238`) y R8 (`:570`): el bloque `auditoria` va «en la
  herramienta de estado que el MCP ya tiene».
- **Este caso:** este MCP tiene `buscar`, `leer` y `lint`, y ninguna es de estado. Sumar una
  agranda la superficie, y la receta misma lo desaconseja para la herramienta `auditoria` bajo
  stdio (R9, `:597`).
- **Propuesta:** decir qué hace un MCP sin herramienta de estado: el bloque en el log de
  arranque, en el resumen de estado de su herramienta principal, o una herramienta nueva, con el
  criterio para elegir.

## S-06 · La receta no tiene evidencia de adulteración

- **La receta:** nada sobre integridad del registro.
- **Este caso:** cada línea lleva el sha256 de la anterior (`prev`) y hay un verificador que
  detecta una línea cambiada, sacada o agregada en el medio. Sus límites están declarados: sin
  clave, quien sepa calcular sha256 puede rehacer la cadena entera, y lo cortado del final no se
  ve. Cerrarlo pide mandar el registro fuera de la máquina.
- **Propuesta:** evaluarlo como regla opcional para los MCP donde lo forense importa, o
  declarar por qué no va.

## S-07 · `config/auditoria.toml` en Node exige una dependencia nueva

- **La receta:** la regla 5 y R11 (`:529`, `:618`): las listas van en `config/auditoria.toml`.
- **Este caso:** Node no trae un lector de TOML. Sumar uno cambia la lista de dependencias, que
  en este proyecto está aprobada por huella. La alternativa es un parser propio del subconjunto.
- **Propuesta:** aceptar el mismo contenido en JSON, o fijar el subconjunto de TOML que usa el
  archivo (tablas, tablas en línea, cadenas, enteros y booleanos) para que un hermano lo pueda
  leer con un parser chico y probado.

## S-08 · Sin CI no hay PASS posible

- **La receta:** la regla 9 (`:360`): «Verificar que exista un runner…». El perfil MCP de
  MapaObjetivo, en el paso 8, agrega: «Sin el runner del 7 no se escribe PASS».
- **Este caso:** el proyecto corre en la PC de la operadora, sin CI (`CI=NINGUNA`), y su portón
  corre bajo su autorización. Ahí `TESTS_FUGA=PASS` no se puede escribir nunca, aunque la suite
  y la E2E corran sobre cada candidato y su salida quede anotada.
- **Propuesta:** decir qué cuenta como «equivalente» de un runner, o asumir explícitamente
  NO_ACREDITADO con conformidad para los proyectos sin CI.


## Segunda entrega (2026-10-04): lo medido al aplicar la receta

Sale del incremento 7 del proyecto: la auditoría reconstruida con la receta (cortes 7a a 7f,
commit `b840538`). El paquete se corrió desde su fuente en `0d2dc35`, sin instalarlo. Cada fila
dice si está **medida** o sólo leída; el detalle está en las reconciliaciones del proyecto
(`docs/refactor/reconciliacion-7b-archivo.md` a `-7f-kit-y-lectores.md`) y en el §6 de
`docs/plan-incremento-7.md`, de donde salen estas filas tal cual.

| | Qué | Dónde se ve |
|---|---|---|
| S-09 | R4 nombra cuatro valores del activador (vacío o `0`, `1`, `crudo`, una ruta absoluta), y el paquete acepta además `false`, `no`, `true`, `si`, `yes`, `crude`, `debug` y `raw`. Este contrato sigue al paquete. Lo vio la revisión par (seconbrian-66) | `SKILL.md:516` · `registro.py:44-46` |
| S-10 | R3 dice `arnes{id, proyecto}`, y el paquete escribe `{id, sesion, proyecto}`. Este contrato sigue al paquete. Lo vio la revisión par | `SKILL.md:493` · `arneses.py:83` |
| S-11 | Con la ruta absoluta de R4, la carpeta no se autoprotege: `ruta()` no pasa por `directorio_por_defecto()`, que es la que escribe el `.gitignore`. **Y más (7c, leído, no corrido):** si esa ruta todavía no existe, `ruta()` la toma por base de nombre de archivo, y escribe `lucky-secondbrian-registro_auditoria-<sesión>.jsonl` en la carpeta de arriba. Con `<bóveda>/registro_auditoria` recién configurada, eso es la raíz de la bóveda | `registro.py:279-306` |
| S-12 | El retorno sólo admite cuentas. Una palabra de un conjunto cerrado (la `evidencia` de `buscar`, `normal` o `baja`) no se puede declarar, aunque no filtre nada | `redaccion.py`, `retorno_de` |
| S-13 | `cazar` decide que una respuesta es un fracaso sólo por `ok: false`. A un MCP que marca el error con `isError`, como este, le devuelve sus errores como candidatos. **Medido en el 7f** (`scripts/banco-lectores.ts`): sobre una sesión cruda de este servidor, `cazar` devuelve como candidata la `ruta` del NO_EXISTE de `leer`, cuya línea dice `resultado: "error"` y cuyo cuerpo es `{codigo, mensaje, pedido}`, sin `ok`. `afirmaciones` usa el mismo criterio (`:199`). Y el enganche del propio paquete para el SDK 1.x anota un `isError` como `error: "IS_ERROR"` (`enganches/mcp1x.py:93-94`, leído): su escritor y su lector tampoco coinciden, como los que `rechazos.py:9-12` da por arreglados para `ok: false`. Que `cazar` y `afirmaciones` salteen las líneas con `resultado: "error"` | `lectores.py`, `_es_un_fracaso` (`:154`) y `:97` |
| S-14 | En stdio el escritor es el id del arnés: dos procesos de la misma sesión (una reconexión) comparten archivo, y el paquete sólo tiene candado entre hilos. **Medido en el 7b, en este adaptador:** con un candado por archivo, dos procesos de la misma sesión dejan un archivo con una cabecera cada uno y la cadena cierra; contra un build sin el candado, el banco vio 5 fallas en la cadena. El paquete no se corrió | `identidad.py`, `escritor()` · [`refactor/reconciliacion-7b-archivo.md`](refactor/reconciliacion-7b-archivo.md) |
| S-15 | Para R5 («`roots/list` · otros clientes: pendiente»), medido bajo stdio. Claude Code 2.1.289 declara `roots` y responde dos: el proyecto y la carpeta del usuario. Codex 0.160.0 no los declara | [`diagnosticos/2026-10-04-entorno-de-los-clientes.md`](diagnosticos/2026-10-04-entorno-de-los-clientes.md) |
| S-16 | Codex 0.160.0 les vacía el entorno a sus servidores (20 variables fijas y el `env` de su configuración): no hay testigo para el catálogo ni proyecto para R1. Con la receta tal cual, Codex no audita; necesita la ruta absoluta de R4. Que la receta lo nombre en el catálogo o en R1 | [`diagnosticos/2026-10-04-entorno-de-los-clientes.md`](diagnosticos/2026-10-04-entorno-de-los-clientes.md) |
| S-17 | Claude Code le pasa `CLAUDE_CODE_MESSAGING_TOKEN` a cada servidor MCP. La lista blanca de la regla 2 lo protege; conviene que el kit lo use como centinela con ese nombre | [`diagnosticos/2026-10-04-entorno-de-los-clientes.md`](diagnosticos/2026-10-04-entorno-de-los-clientes.md) |
| S-18 | Claude Code pone `AI_AGENT`, que nombra el producto y la versión (`claude-code_2-1-289_agent` en la extensión). No se midió si llega a los servidores: estaba en el padre de la medición. Lo vio la revisión par | [`diagnosticos/2026-10-04-entorno-de-los-clientes.md`](diagnosticos/2026-10-04-entorno-de-los-clientes.md) |
| S-19 | El id de sesión del arnés va al nombre del archivo sin validar: `leer()` lo copia tal cual y `escritor()` lo devuelve. Con un separador, `Path.with_name` levanta `ValueError`, y `ruta()` corre fuera del `try` de `_escribir`: `registrar()`, que promete «nunca levanta», levanta, y `estado()` también. Medido con `pathlib`; el paquete no se corrió. Claude Code da un UUID, así que hoy no pasa. Este adaptador valida el id y, si no sirve de nombre, firma el archivo con el acuñado (fila 1 de la reconciliación del 7b) | `arneses.py:64-69` · `identidad.py:138-148` · `registro.py:306` y `:378` |
| S-20 | La regla 4 enumera tres caminos de error, y falta un cuarto: el SDK rechaza el pedido entero con un error JSON-RPC, antes de su manejador. En el SDK de TypeScript, `setRequestHandler` valida `params` contra el esquema de `tools/call` y lanza si no cumple (sin `name` de texto, sin `params`, `arguments` que no es un objeto). Un enganche que sólo mira lo que vuelve no deja línea. En el SDK de Python no se midió. Lo encontró la revisión par en el 7b | `@modelcontextprotocol/sdk` 1.30.1, `shared/protocol.js:889-891` · fila 14 de la reconciliación del 7b |
| S-21 | `_escribir` marca la cabecera como escrita antes de escribirla. Si esa escritura falla, o si `_cabecera()` levanta, las líneas que siguen del mismo proceso salen sin cabecera. Lo vio la revisión par; leído, no corrido. Este adaptador la marca después de escribir | `registro.py:430-434` |
| S-22 | El paquete compara sin mayúsculas sólo las palabras del crudo (`valor.lower() in _PALABRAS_CRUDAS`); las de apagado y redactado, con mayúsculas. `TRUE`, `Si` o `YES` le apagan la auditoría, con el aviso «no es una palabra conocida ni una ruta ABSOLUTA». Este adaptador compara todas sin mayúsculas (7c) | `registro.py:144-151` |
| S-23 | `cargar` no valida `largo_max` ni `elementos_max`. Con `largo_max = "500"` la redacción carga y rige, y `argumentos_de` levanta `TypeError` al comparar: `registrar()`, que promete «nunca levanta», levanta, y con él la llamada en el enganche. **Medido** con el paquete corrido desde su fuente (7d). Este adaptador cierra la redacción | `redaccion.py`, `_valor_seguro` y `cargar` · `registro.py`, `registrar` |
| S-24 | `cargar` no mira las claves adentro de cada sección ni su tipo: `opaca` por `opacas`, `largo` por `largo_max` u `opacas = "buscar"` cargan, y la regla no rige. Con los de `[herramientas]`, `buscar` deja de ser opaca y anota el largo de la consulta. **Medido** (7d). El molde de este repo promete cerrar ante una clave que no se conoce, y el adaptador lo cumple | `redaccion.py`, `cargar` |
| S-25 | La huella es `sha256(str(valor))`, con el `str()` de Python: `True`, `1e-07`, `['a', 1]`. En escalares un hermano lo reproduce (este adaptador lo hace, con 18 vectores); en listas y diccionarios, no. Que la receta la defina sobre un texto canónico, JSON con claves ordenadas, por ejemplo. Y `JSON.parse` no distingue 5 de 5.0: un `float` declarado no coincide igual en los dos lados. Más evidencia para S-01 | `redaccion.py`, `huella` |
| S-26 | Con la redacción cerrada, una herramienta opaca deja de serlo: `argumentos_de` sólo mira `opacas`, que queda vacía, y anota los nombres de los campos y sus largos. «Cerrada» es menos privada que «abierta» justo en las herramientas de texto libre. **Medido** (7d). Que la cerrada anote `{_opaco: true}` para toda herramienta, o que la receta lo diga. Este adaptador lo hace desde el seguimiento par del 7d: aplica la decisión del 6 («nunca las consultas») | `redaccion.py`, `Redaccion.cerrada` y `argumentos_de` |
| S-27 | La salida del CLI en Windows. `cli.py:44` imprime con `ensure_ascii=False`, y por un pipe Python escribe en la página de códigos de la consola (cp1252 en esta PC), no en UTF-8. Con una `ñ` la salida deja de ser UTF-8, y la clave `señales` de `afirmaciones` (`lectores.py:223`) la lleva siempre. Con un carácter que esa página no tiene (`Ł` en el proyecto), `por-sesion` se cae: `UnicodeEncodeError`, exit 1 y stdout vacío. Es justo el uso que declara el CLI: encadenarlo con otra cosa. **Medido** (7f). Que escriba UTF-8 siempre, o `ensure_ascii=True` | `cli.py:44` |
| S-28 | `cli.py:31` deja los comodines al shell, y el uso del README (`*.jsonl`, `README.md:302-304`) no anda en PowerShell ni en cmd, que los pasan tal cual: `no existen: *.jsonl`, exit 2. En Git Bash sí. **Medido** en PowerShell (7f). Además, la línea de `cazar` del README apunta todavía a `<estado>/registro_auditoria/<proyecto>/`, la carpeta de antes de R1. Que el CLI expanda él lo que no exista tal cual | `cli.py:31` · `README.md:302-304` |
| S-29 | `por-sesion` suma los MCP de un mismo proyecto. Agrupa por `sesion`, y las líneas no dicen qué MCP las escribió: el nombre va sólo en la cabecera (`registro.py:323`), que `leer()` descarta (`lectores.py:30`). Por R1, todos los MCP de un proyecto escriben en la misma `registro_auditoria/`, con el mismo id de sesión del arnés: dos `buscar` de dos MCP salen como `{"buscar": 2}`. Y `desde`/`hasta` son la primera y la última `cuando` en orden de lectura, no el mínimo y el máximo: con dos archivos, `desde` (10:00:09) quedó después de `hasta` (10:00:05). **Medido** (7f). Que `leer()` arrastre el MCP de la cabecera, y que se tomen el mínimo y el máximo | `lectores.py:30` y `:254-278` · `registro.py:323` |
| S-30 | `registro.py:22-23` promete que «un lector que encuentra un número que no conoce puede decirlo», y `lectores.py:30` descarta la cabecera sin mirar `esquema`. Un archivo con `esquema: 99` se lee igual, sin un aviso. **Medido** (7f) | `registro.py:22-23` · `lectores.py:30` |
| S-31 | `rechazos` lee sólo `retorno.fallaron` (`lectores.py:240`), un nombre que cada anfitrión elige en su `auditoria.toml` (el molde lo sugiere, `auditoria.toml.example:115` y `:122`) y que nada valida. Con `fallidos`, devuelve vacío y no avisa. Para este servidor no importa: no tiene herramientas por lote. **Medido** (7f). Que la receta fije el nombre, o que `cargar` lo valide | `lectores.py:240` |

**Más evidencia para S-01.** Los tipos de `describir` son nombres de Python (`str`, `dict`), y
`cuando` sale con `+00:00` en Python y con `Z` en TypeScript. Sin especificación, un hermano copia
esas formas leyendo el código.

Las líneas citadas son de `0d2dc35`.

---
Lo deja la sesión que aplica la receta; lo procesa la sesión custodia de `lucky-skills`.

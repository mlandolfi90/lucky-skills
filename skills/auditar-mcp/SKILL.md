---
name: auditar-mcp
description: Construir auditoría interna en un MCP para atribuir cada llamada a su sesión. Usar al construir o revisar un MCP cuyo backend comparten varias sesiones con credencial única.
---

# Auditar MCP

Hacer atribuible cada llamada de herramienta de un MCP compartido, sin que el
registro fugue secretos ni mienta sobre resultados. Forense, no defensa: el
registro responde "quién y qué quiso hacer"; no impide nada.

El agujero es estructural, no un descuido: un MCP típico es una pasarela
fina que se apoya en lo que dice el servidor, y cuando el servidor no
atribuye (credencial compartida, sin logs de acceso), nadie atribuye — el
MCP es el único punto donde existe la tripleta sesión→intención→llamada.
Por lo mismo, una pasarela sin registro tampoco puede auditarse en su
propia fidelidad: respuestas que afirman más de lo que pasó solo se ven
comparando lo que entró con lo que salió. Frontera con logalizar:
logalizar mira hacia adentro de una lógica propia; auditar-mcp mira el
borde — y en una pasarela, el borde es casi todo lo que hay.

## Invariantes

- **Medir antes de elegir el patrón.** Ante resultados no atribuibles hay
  tres respuestas de industria, ordenadas por lo que exigen del servidor:
  clave de idempotencia (requiere servidor), petición-respuesta asíncrona
  202+Location (requiere servidor), reconciliación con registro propio (no
  requiere nada). La elección se decide leyendo el contrato real del
  servidor (OpenAPI, docs), nunca suponiéndolo.
- **Medir cómo reacciona el servidor a un pedido repetido**: rechaza
  (reintento seguro), duplica (ensucia visible) o renombra en silencio
  (éxito + daño a la vez — el peor). Si el servidor puede reescribir lo
  enviado, eso no sirve como identidad: reconciliar contra una foto de ids
  tomada ANTES de operar.
- **La identidad se acuña en el propio MCP.** Con transporte stdio el
  proceso ya es la sesión: uuid + pid + iniciada + cwd, en un módulo
  importado una vez. El nombre del cliente (`claude-code`) nombra al
  producto, no a la sesión; el `cwd` es lo que separa espacios de trabajo.
  Declarar el límite: el nombre bonito de la sesión no viaja por el
  protocolo — el registro separa por espacio de trabajo, no por sesión.
- **Un solo punto de enganche**: el middleware del framework, nunca decorar
  herramienta por herramienta — la herramienta N+1 nace auditada. Un gancho
  declarado no es un gancho que corre: probarlo en aislamiento antes de
  construir encima. Todo lo leído del contexto va defensivo (getattr +
  try): auditar jamás puede romper una llamada.
- **Un error devuelto también es un error.** En MCP el fallo idiomático es
  una respuesta de error, no una excepción; sin esto el registro anota "ok"
  sobre rechazos. Parsear el código de error de la respuesta (JSON, no
  búsqueda de palabra) y anotar solo el código, nunca el mensaje.
- **Lista blanca de argumentos, no lista negra**: protege lo que aún no se
  inventó. Lo no declarado se reduce a forma (tipo + largo); herramientas
  de texto libre (ssh, console, http) son opacas hasta en el tamaño — el
  largo mide una password. Nombres genéricos en la lista blanca valen para
  todas las herramientas futuras: cada excepción lleva su motivo escrito al
  lado. Del error, el tipo o código; jamás el mensaje. Rige
  custodiar-secretos.
- **Un archivo por escritor**: el id de sesión va en el nombre del archivo,
  incluso con ruta explícita configurada. Un candado entre procesos
  administra la pregunta; el nombre la elimina. JSONL, y una función que
  responda dónde escribe. El archivo va al .gitignore.
- **Apagado por omisión**: escribir en disco lo decide el operador vía
  variable de entorno. Comprobar si algo regenera el archivo donde vive el
  interruptor: un interruptor que se apaga solo es peor que no tenerlo.
- **Modo crudo: suspende la redacción, y lo dice.** Para depurar hace falta
  ver el argumento mandado Y la respuesta entera en la misma línea (única
  prueba de que un parámetro llegó y se descartó en silencio). Un "casi
  crudo" que redacta un poco no sirve y da falsa seguridad: o redacta, o
  no. El precio: el archivo pasa a ser material sensible. Un modo que
  suspende la redacción tiene que ser imposible de encender por inercia e
  imposible de confundir encendido: se activa con una palabra (`crudo`),
  nunca con `1`; el archivo se llama distinto y a gritos
  (`auditoria-CRUDA-…`); cada línea lleva `"modo":"crudo"` (la marca viaja
  con el contenido pegado suelto); y un WARNING en el log del proceso al
  primer uso — contra el interruptor olvidado de una sesión anterior. Es el
  punto donde auditar se vuelve logalizar y hereda sus obligaciones:
  temporal, con fecha de apagado, se borra al terminar.
- **El registro se prueba con fallos, no solo con éxitos**: secreto
  centinela buscado en el texto crudo, parámetro inexistente, opacidad sin
  tamaño, mensaje de excepción no copiado, apagado que no escribe, fallo de
  escritura que no levanta, y un E2E contra proceso real — lo único que
  descubre ganchos que no disparan.
- **El registro declara su propio alcance**: qué anota, qué no, y por qué.

## Flujo

1. Medir el contrato del servidor y su reacción al pedido repetido; elegir
   el patrón por descarte medido.
2. Acuñar identidad de sesión en el MCP; verificar por medición qué campos
   del contexto llegan de verdad (y con qué nombre).
3. Enganchar el middleware único; ejercitarlo con llamadas que fallan.
4. Diseñar la redacción por lista blanca con sus excepciones motivadas.
5. Interruptor apagado por omisión; verificar quién regenera su archivo.
6. Suite con los tests de fuga; E2E contra proceso real.
7. Declarar lo que queda afuera (p. ej. identidad propia contra el
   servidor: usuarios/ACL por espacio de trabajo, con su riesgo de
   deny-all si la ACL nace vacía).

## Referencia viva

Implementación verificada en vivo: repo `lucky-tool-gns3`, commits
`8abbf6f`, `982835c`, `3a3f8b8`, `01c11a7`, `e42988c` — anclar ahí, no a
rutas de archivos, que se mueven. Leer los cinco en orden: los cuatro
últimos son huecos aparecidos después de que la primera versión ya estaba
"terminada" — el material de qué revisar cuando parece listo.

## Salida

```text
PATRON=IDEMPOTENCIA|ASYNC|RECONCILIACION
MEDICION_SERVIDOR=<contrato leído y reacción a repetido>
IDENTIDAD=<campos acuñados y su límite declarado>
ENGANCHE=MIDDLEWARE|BLOCKED
REDACCION=WHITELIST
TESTS_FUGA=PASS|FAIL
INTERRUPTOR=OFF_POR_OMISION
ALCANCE_DECLARADO=...
```

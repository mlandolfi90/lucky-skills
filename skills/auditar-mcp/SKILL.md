---
name: auditar-mcp
description: Construir auditoría interna en un MCP para atribuir cada llamada a su sesión y depurar la pasarela. Usar al construir o revisar un MCP cuyo backend comparten varias sesiones con credencial única.
---

# Auditar MCP

Hacer atribuible cada llamada de herramienta de un MCP compartido y usar ese
registro para mejorar y depurar la pasarela, sin que el registro fugue
secretos ni mienta sobre resultados. Lo forense (quién hizo qué) es lo que
no tiene reemplazo; lo que más rinde es la depuración.

El agujero es estructural, no un descuido: un MCP típico es una pasarela
fina que se apoya en lo que dice el servidor, y cuando el servidor no
atribuye (credencial compartida, sin logs de acceso), nadie atribuye — el
MCP es el único punto donde existe la tripleta sesión→intención→llamada.
Por lo mismo, una pasarela sin registro tampoco puede auditarse en su
propia fidelidad: respuestas que afirman más de lo que pasó solo se ven
comparando lo que entró con lo que salió. Frontera con logalizar:
logalizar mira hacia adentro de una lógica propia; auditar-mcp mira el
borde — y en una pasarela, el borde es casi todo lo que hay.

Toda regla de abajo nació de una medición en un repo real y varias se
cayeron al cambiar de transporte o de SDK. Ninguna se aplica sin medirla
en el MCP que se está construyendo.

## Reglas de desarrollo

### 1. Medir antes de elegir el patrón

- Ante resultados no atribuibles hay tres respuestas de industria,
  ordenadas por lo que exigen del servidor: clave de idempotencia
  (requiere servidor), petición-respuesta asíncrona 202+Location (requiere
  servidor), reconciliación con registro propio (no requiere nada). Se
  elige leyendo el contrato real (OpenAPI, docs), nunca suponiéndolo.
- Medir cómo reacciona el servidor a un pedido repetido: rechaza (reintento
  seguro), duplica (ensucia visible) o renombra en silencio (éxito + daño a
  la vez — el peor). Si puede reescribir lo enviado, eso no sirve como
  identidad: reconciliar contra una foto de ids tomada ANTES de operar.
  Medir puede QUITAR requisitos, no solo agregarlos: un servidor que
  rechaza no necesita la foto previa. Y "rechaza" puede depender de un
  ajuste apagable del servidor: medir el ajuste, no solo la respuesta.

### 2. Identidad: se acuña en el MCP, y se mide de dónde sale

- El proceso del MCP es el único componente que uno controla y que ve la
  llamada. La identidad se acuña ahí (uuid + pid + iniciada), en un módulo
  importado una vez. Trampa nombrada: el `session_id` del framework puede
  ser un UUID nuevo por llamada (fastmcp 4 bajo stdio reconstruye la
  conexión por pedido); es el campo que uno agarra primero y el que no
  sirve. El nombre del cliente (`claude-code`) nombra al producto, no a la
  sesión.
- Antes de darse por vencido con la sesión, medir el ENTORNO del proceso
  hijo: el arnés puede heredarle el id exacto de la conversación y la raíz
  del proyecto (en Claude Code: `CLAUDE_CODE_SESSION_ID`,
  `CLAUDE_PROJECT_DIR`). Es un canal por producto, no un estándar: se
  modela como catálogo de arneses, cada uno declarando su variable
  testigo, sus campos y su límite. Sumar un arnés no toca código
  compartido. Bajo HTTP el protocolo trae `mcp-session-id` y no hay que
  acuñar nada.
- Medir el `cwd` del proceso, no asumirlo: hay lanzadores que lo ponen en
  `%TEMP%` para todos los espacios de trabajo, y entonces no separa nada.
- El entorno que trae la identidad también trae secretos (tokens del
  arnés). La fuente de identidad necesita su propia lista blanca: la
  declaración del arnés ES la lista, ningún otro código lee `os.environ`,
  y una prueba prohíbe por clase que una variable declarada contenga
  TOKEN/SECRET/KEY/PASSWORD/CREDENTIAL.
- Medir cuántas sesiones atiende un proceso, porque es una propiedad del
  transporte: stdio = una (el stdin/stdout lo creó quien lanzó; dos
  clientes no pueden compartirlo); streamable-http = muchas. Todo lo que
  sigue depende de esa cuenta.

### 3. Enganche: un solo punto, verificado contra la tabla de ruteo

- La propiedad que sobrevive a los SDK es "el punto por donde pasa todo
  `tools/call`", no "el middleware del framework" — conviven bases
  incompatibles (`mcp` 1.x sin middleware, `mcp` 2.x con middleware,
  `fastmcp` 4.x con hooks). Se usa la vía de extensión del framework
  elegido; nunca decorar herramienta por herramienta: la N+1 nace
  auditada.
- Un gancho declarado no es un gancho que corre: probarlo en aislamiento.
  Y un test que llama al override directo pasa por definición: la guarda
  invoca el handler REGISTRADO en la tabla de ruteo del servidor, para que
  falle si el SDK deja de ligarlo. Si el framework trae un cliente en
  proceso que hace un `tools/call` real por toda la pila, la guarda
  "¿el gancho dispara?" se muda del E2E a la suite y cuesta milisegundos.
- El mismo principio vale para el ACCESO al framework: todo lo que toque
  su inventario privado pasa por una función, con una guarda (AST) que
  impide que vuelva a dispersarse. Factura medida al migrar de SDK: el
  port tocó esa función y cero guardas; 737 de 747 tests en verde en la
  primera corrida.
- Todo lo leído del contexto va defensivo (getattr + try): auditar jamás
  rompe una llamada. Del contexto del transporte se saca un campo por
  nombre, nunca el diccionario: los headers HTTP traen `authorization`.
- Los nombres de los campos del contexto se miden, no se suponen: el
  protocolo dice `clientInfo`, el SDK puede exponer `client_info`; el
  error da forma correcta con contenido vacío, sin fallar.

### 4. Desenlace: un error tiene tres caminos, y el tipo se busca al fondo

- Un error devuelto también es un error, y es estructural, no una carencia
  de un SDK: el `is_error` del framework marca SUS excepciones, no los
  rechazos de la pasarela — un `{"ok": false}` del dominio llega con
  `is_error=False`, porque ningún framework puede saber que ese retorno es
  un error. Creerle anota "ok" sobre el 100% de los rechazos. Los caminos
  son tres: excepción;
  retorno con `is_error` (sin excepción, el código viaja en el contenido);
  y retorno normal que trae el rechazo adentro (`{aplicadas:0,
  rechazadas:3}` — la forma normal de cualquier tool por lote). Los dos
  primeros los decide el gancho; el tercero se ve porque el resumen del
  retorno pasa por su lista blanca (regla 5) y queda al lado del estado:
  el estado habla de la llamada, el resumen de cada ítem.
- Parsear el código de error (JSON), no buscar la palabra: un texto que
  menciona `error_code` no es un fallo.
- Del error, el tipo o el código; jamás el mensaje, que arrastra los
  argumentos. Pero medir si el framework envuelve: en fastmcp 4 el tipo de
  afuera es siempre `ToolError` y el registro queda coherente y vacío. El
  error real sobrevive en `__cause__`: recorrer la cadena hasta el fondo,
  con tope de iteraciones (una cadena circular cuelga el servidor). El
  envoltorio sirve cuando difiere: `ToolError` sobre `PlanNotFound` dice
  "el dominio lo rechazó"; `NotFoundError` pelado dice "tool inexistente".
- El middleware re-lanza sin envolver. Y aparte del registro, medir qué
  recorta el framework antes de que el error llegue al modelo (en fastmcp,
  `mask_error_details` explícito); es otra superficie, no la del log.

### 5. Redacción: listas blancas, por forma, y una por superficie

- Lista blanca, no lista negra: protege lo que aún no se inventó. Medir la
  superficie antes de discutir: contar los nombres de argumento distintos
  que existen de verdad suele dar un número chico y convierte el debate en
  una cuenta.
- Un campo es seguro por nombre + tipo + tope de largo, no por nombre: el
  tipo lo elige el cliente y el registro anota ANTES de que nadie valide
  — medido, no supuesto: con fastmcp 4.0.3 la línea se escribe con el
  valor rechazado adentro; si el gancho escribiera post-validación, la
  lista por tipo sería una precaución teórica y su test pasaría igual
  sin cubrir la fuga. `lineas="<secreto>"` donde se esperaba un int llega
  al disco si la lista solo mira el nombre.
- La lista blanca protege el REGISTRO, no el proceso: el registro puede
  estar limpio y el proceso haber filtrado igual, y el archivo de
  auditoría no es evidencia sobre las otras superficies. Medido en
  fastmcp 4.0.2 y 4.0.3 (dos puntos, no una serie): un argumento con tipo
  inválido ni llega a la tool — el gancho anota la línea con el argumento
  reducido a forma y el archivo queda LIMPIO — pero el valor entero sale
  por DOS puertas: el WARNING del framework en stderr (`Invalid arguments
  for tool 'x': [{... 'input': '<el secreto>'}]`) y el error que recibe
  el agente (`input_value='<el secreto>'` dentro del `ToolError`), o sea
  que vuelve al modelo. `mask_error_details` no tapa ninguna de las dos
  (probado con True y con False: idéntico). La puerta de stderr pasa por
  `logging`, pero no se ve desde la raíz: el logger `fastmcp` tiene
  `propagate=False` con handlers propios, y un handler en la raíz captura
  cero — la trampa es instrumentar la raíz, ver nada y concluir que no
  pasa por logging; un `logging.Filter` sobre el logger `fastmcp` sí la
  ataja. Para la puerta del error devuelto no hay interruptor. Hermana
  de `mask_error_details` (regla 4) y del precedente de uvicorn con el
  `?token=` en claro. Lo que no coincide con la forma declarada cae a
  descripción (`{tipo, largo}`); una guarda compara la forma declarada
  contra el esquema que el servidor publica.
- La lista es por nombre de campo y vale para todas las herramientas
  futuras: los nombres genéricos (`x`, `name`) son decisiones con su motivo
  escrito al lado, no defaults.
- Herramientas de texto libre (ssh, console, http, tftp) son opacas hasta
  en el tamaño: el largo de lo tipeado mide una password.
- El retorno necesita su propia lista, con el defecto invertido: un
  argumento no declarado se anota reducido a forma (omitirlo deja al
  registro mintiendo sobre lo pedido); un retorno no declarado NO se anota
  ni en forma (anotarlo de más convierte el registro en copia del
  inventario). Misma palabra, decisión opuesta según el lado.
- Trato `huella` (sha256 corto) para credenciales que hay que
  correlacionar sin guardar. Se aplica en los DOS lados o no correlaciona
  nada: la credencial nace en un retorno y se usa en un argumento.
- El redactor falla cerrado ante cualquier problema, incluida una forma
  inesperada de su propia configuración, y eso se prueba: auditar tampoco
  puede romper el ARRANQUE. Caso nombrado: `por_defecto = "completo"` deja
  la lista escrita y sin efecto; el archivo parece configurado.
- Una regla con respaldo permisivo es la regla que el respaldo dice, no
  la que el docstring dice. Y avisar no es actuar: si la guarda detecta y
  sigue, la guarda no existe — es una nota en un log que nadie mira. Los
  dos defectos de R1/R4 fueron eso: la protección existía y el camino de
  respaldo la anulaba, y el segundo se escribió corrigiendo el primero.
- Rige custodiar-secretos en todo el carril.

### 6. Archivo: el nombre dice quién escribió; la sesión va en cada línea

- El nombre identifica al ESCRITOR; la sesión identifica la LLAMADA y va
  en cada línea. Bajo stdio proceso == sesión y el id también puede ir en
  el nombre; bajo HTTP un proceso atiende N sesiones y ponerlas en el
  nombre da N archivos abiertos para una colisión que no existe (el
  candado de hilos ya ordena a los escritores de un proceso).
- Marcas que van SIEMPRE en el nombre, incluso con ruta explícita: el
  nombre del MCP adelante (`ls` agrupa por herramienta; `cat
  <mcp>-auditoria-*.jsonl` junta los de uno) y la marca de crudo cuando
  corresponde (`<mcp>-auditoria-CRUDA-…`): quién escribió y que está sin
  redactar son dos cosas y las dos se leen de un vistazo. Si la ruta
  configurada ya nombra al MCP, no se repite.
- El nombre del MCP se deriva de la distribución instalada, nunca de una
  constante a mano: la skill se aplica copiando, y una constante copiada
  hace que dos MCP escriban con el mismo nombre. Medir si la instalación
  lo permite: en modo editable (como corre un MCP en desarrollo) suele no
  haber camino del paquete a la distribución; ahí la constante se ata al
  manifiesto (`[project].name`) con una prueba que en una copia falla.
  Segunda fuente válida: el nombre que el servidor declara a sus clientes.
- Lo que el enganche garantizaba por construcción viaja con él o se vuelve
  parámetro obligatorio: al mover el enganche (de subclase a middleware)
  la declaración del nombre se cayó y nada falló — el registro escribió
  `mcp-sin-nombre-auditoria-…`, forma correcta y origen equivocado. Un
  middleware sin nombre no se puede construir.
- JSONL, una línea por llamada; una función que responda dónde escribe
  (los tests la usan). La cabecera se escribe con la primera línea, no al
  arrancar: un servidor que nadie usó no deja rastro.
- Al `.gitignore` con patrón `*auditoria-*.jsonl`: el prefijo del MCP
  rompe el patrón sin comodín adelante, y olvidarlo commitea material
  sensible.

### 7. Interruptor: apagado por omisión, y con salida visible

- Escribir en disco lo decide el operador vía variable de entorno; sin
  ella, apagado de verdad: ni archivo vacío ni directorio creado. La
  prueba necesita un `chdir` a un directorio limpio: un interruptor mal
  escrito no deja de escribir, escribe con el directorio VACÍO — en el
  cwd — y una prueba que mira `tmp_path` pasa con el interruptor roto.
  Comprobar quién regenera el archivo donde vive: un `.env`
  reescrito entero desde el gestor de secretos apaga el interruptor en
  silencio, y un interruptor que se apaga solo es peor que no tenerlo. Va
  donde no lo regeneren (p. ej. el bloque `env` del registro del cliente).
- Medir por dónde llega el `.env` al proceso: según el mecanismo de carga,
  una variable puede quedar en las settings del framework sin exportarse a
  `os.environ` (y descartarse en silencio por `extra="ignore"`), o llegar
  a todo. No generalizar de un repo a otro.
- La herramienta de estado que el MCP ya tiene informa la auditoría: modo
  activo, ruta del archivo de esta sesión, aviso si está en crudo, y el
  acumulado del DIRECTORIO (archivos, crudos, bytes) — no del archivo
  propio, porque la pregunta es la del que se olvidó de apagarlo hace tres
  días. Va en la herramienta de estado y no en una nueva: una dedicada a
  "¿cómo está la auditoría?" no la llama nadie, que es por lo que el
  problema existía. Si contar falla, informa el tipo de error y no tumba
  el `check`.

### 8. Modo crudo: suspende la redacción, y lo dice

- Para depurar hace falta ver el argumento mandado Y la respuesta entera
  en la misma línea (separados no se cruzan). Un "casi crudo" que redacta
  un poco no sirve y da falsa seguridad: o redacta, o no. Mientras el MCP
  está en desarrollo, el crudo es el modo de trabajo, no una escotilla; el
  formato se decide por él.
- El precio: el archivo pasa a ser material sensible. Un modo que suspende
  la redacción tiene que ser imposible de encender por inercia e imposible
  de confundir encendido: se activa con una palabra (`crudo`), nunca con
  `1`; el archivo se llama distinto y a gritos; cada línea lleva
  `"modo":"crudo"` (la marca viaja con el contenido pegado suelto); WARNING
  en el log del proceso al primer uso — y como eso es una vez por proceso
  y nadie mira el log, el acumulado de la regla 7 es lo que lo recuerda.
- Es el punto donde auditar se vuelve logalizar y hereda sus
  obligaciones: temporal, con fecha de apagado, se borra al terminar.

### 9. Pruebas: de fuga, en los dos modos, y con un guardián que las corra

- La mayoría de los tests son de fuga, no de formato: secreto centinela
  buscado en el TEXTO CRUDO del archivo (no en el objeto parseado), por
  cada camino; parámetro que no existe (la razón de ser de la lista
  blanca); opacas sin tamaño; mensaje de excepción no copiado; apagado que
  no escribe; fallo de escritura que no levanta; marcas del nombre con
  ruta explícita.
- Las guardas son conscientes del modo, con expectativa invertida: en
  redactado el centinela NO aparece; en crudo SÍ debe aparecer. Sin la
  segunda, una redacción rota que borra todo pasa en verde y el modo de
  depurar deja de depurar sin que nadie lo note. Una guarda que solo
  prueba ausencia se cumple sola cuando el código no llegó ahí.
- Ejercitar con llamadas que fallan, por los tres caminos de la regla 4.
  Un registro probado solo con éxitos miente justo cuando importa.
- Cada decisión se prueba por reversión: romperla a mano y verificar qué
  test la caza. Una comprobación redundante no es una guarda y no se le
  puede escribir un test.
- Las guardas se escriben contra la PROPIEDAD, no contra la mitigación
  propia. "Todos los verbos son corrutinas" dio rojo el día que el
  framework empezó a correrlos en hilos por su cuenta, con la propiedad
  cumplida; y borrar esa guarda borraba lo único que avisaría si el
  trabajo dejara de hacerse. La forma que sobrevive: llamar un verbo por
  un cliente real y preguntar en qué hilo corrió.
- Un test que corre una carrera entre las dos condiciones que debería
  separar no es "frágil": a veces mide otra cosa, y envenena un arnés de
  mutación. Se saca la carrera, no se sube el número hasta que ande.
- Una guarda sobre una regla de exclusión usa un objeto que NO esté
  protegido por otra razón: "limpiar no toca el redactado" se probó
  mirando el archivo del propio proceso, que sobrevive porque está EN
  USO y no porque sea redactado — romper la regla no ponía nada en rojo.
  Primo del control que no ejerce la rama, pero distinto: acá la rama
  corre y el objeto está blindado por otro motivo.
- Una simulación lleva un control de que simula: al simular "Python
  3.10" bloqueando `tomllib`, envolver `__import__` no bloqueó nada
  (`importorskip` usa `importlib.import_module`) y dio un falso rojo que
  casi "arregla" código sano; un finder en `sys.meta_path` sí bloquea, y
  se prueba primero que el módulo de verdad no importa. Y un skip que
  deja el CI verde a costa de no medir lo que existía para medir es verde
  en el sentido malo: la comparación se hace contra una expectativa
  escrita a mano que vale en todas las versiones, y el skip queda solo
  para lo que de verdad no existe ahí.
- E2E contra un proceso real, lanzando el binario por su transporte: lo
  único que descubre ganchos que no disparan, campos que están en otro
  lado, y lo que en el mismo proceso no se puede probar — que el
  interruptor VIAJE hasta el hijo, que su ausencia también viaje, que el
  arnés se reconozca del entorno heredado, y que un token centinela del
  arnés no aparezca en el texto del archivo.
- La reversión encuentra huecos en las pruebas tanto como en el código
  (medido: 2 de 7 en un repo). Una prueba que pasa con la decisión rota
  no es una prueba de esa decisión. Y el respaldo permisivo se esconde
  también en el andamiaje: cuatro guardas que monkeypatchean la función
  de la raíz dejan sin mirar justo la función donde vivía la caída al
  cwd.
- Una suite de auditoría que ensucia la máquina cometió el defecto que
  audita: desde que el crudo ignora la ruta elegida (R1), apuntar la
  variable a `tmp_path` ya no alcanza — cada fixture mueve también
  `LOCALAPPDATA` y `XDG_STATE_HOME`, y una guarda de sesión falla si la
  suite dejó un archivo con el centinela fuera del temporal. Medido: los
  tests de crudo dejaban centinelas en el estado real del que corría la
  suite, y se vio mirando el disco, no leyendo los tests.
- Verificar que exista un runner que corra estos tests (CI o equivalente)
  y decirlo si no lo hay. Un test de fuga que nadie corre no es
  protección, es documentación de una intención — y el que se rompe en
  silencio es el que impedía escribir una password en disco. Y LEER su
  resultado, con el comando, antes de afirmar nada sobre él: medido, un
  CI corrió doce veces y las tres últimas en rojo mientras dos sesiones
  escribían "nunca corrió" en el README; y el rojo decía que el piso de
  Python declarado no funcionaba. Un CI rojo que nadie mira es igual que
  uno que no corre, con la diferencia de que este ya avisó.

### 10. Usar el registro: cazar, no solo leer

- Del registro crudo sale una señal mecanizable: "argumento que el cliente
  mandó y cuyo valor no aparece en ningún escalar de la respuesta"
  (comparación por valor, no por substring). Produce CANDIDATOS, nunca
  veredictos: hay argumentos que legítimamente no vuelven, y decidirlo
  exigiría conocer cada verbo. Se tría a mano. La condición de entrada al
  cazador es "no es un fracaso declarado", no "`ok` es verdadero": medido
  sobre 44 líneas reales, 22 no traían el campo `ok` (21 verbos, casi
  todos de lectura), y un cazador que filtra por `ok is True` está ciego
  en la mitad del corpus, justo donde más sirve. Y el umbral de
  "respuesta flaca" no cuenta `ok` como campo útil, o una lectura
  legítima de dos campos cae como flaca.
- Un hallazgo no se cierra arreglando el caso: se convierte en una forma
  que se barre en todo el repo. El registro encuentra uno; la forma
  encuentra los hermanos (p. ej. todo sitio que recorta salida sin decir
  cuánto quedó afuera).
- El registro declara su propio alcance, incluido lo que NO ve: encuentra
  defectos en el borde de una llamada; lo que el MCP DECLARA (el texto de
  instrucciones, las descripciones de herramientas) no lo ve, porque nadie
  llama a una descripción. Esa prosa es superficie aparte: toda afirmación
  del texto expuesto se verifica contra el runtime (`list_tools()`), nunca
  contra otro texto, barriendo por eje (hosts, puertos, versiones,
  nombres de herramientas, promesas absolutas).

### 11. Lo que queda afuera, y se dice

Forense y depuración, no defensa. La otra mitad es identidad propia contra
el servidor (usuarios/ACL por espacio de trabajo en vez de credencial
compartida); si el servidor lo soporta, se mide y se declara aplazado o
hecho. Riesgo conocido: encender una ACL vacía con usuarios no-admin
deniega todo — crear usuarios y entradas ANTES de dejar el admin.

## Receta: valores fijos para todo MCP de la casa

Las reglas de arriba dicen por qué; esto dice qué. Se aplica igual a un
MCP nuevo, a uno ya nacido o a uno copiado: la puerta está abierta, no es
requisito de nacimiento. Lo que es igual en todos vive en un paquete
compartido (`lucky-auditoria`); lo que se mide en cada uno vive en su
`config/`.

- **R1 — Dónde se guarda: todo archivo de la auditoría, sin excepción,
  va a `<CLAUDE_PROJECT_DIR>/registro_auditoria/`.** Sea cual sea el modo
  (redactado o crudo) y sea cual sea el MCP: una sola carpeta por
  proyecto, así se ubica por proyecto y se limpia por proyecto. Es una
  decisión del humano, cerrada: los argumentos técnicos se resuelven
  adentro de ella, no moviéndola. Cómo se cumple:
  - **El proyecto es el que llamó.** El proceso hijo recibe la raíz de la
    sesión por el entorno (`CLAUDE_PROJECT_DIR` en Claude Code; el
    catálogo de arneses de la regla 2 dice la variable de cada uno) y, si
    el arnés no la da, el protocolo permite pedirle al cliente sus
    `roots`. Sin ninguna de las dos no se escribe en ningún otro lado: se
    apaga y se dice en el log, una vez por proceso. Ni estado del usuario,
    ni cwd (medido: el cwd es lo que el lanzador le dejó al hijo —
    `%TEMP%`, o el repo de otro —, no una propiedad del proyecto).
  - **La carpeta se protege sola.** El paquete escribe adentro un
    `.gitignore` con `*` la primera vez que la crea: ningún repo puede
    commitearla con un `git add -A`. Lo que un `.gitignore` no cubre — un
    zip, un rsync, un `COPY .` de Docker, un sdist — se cubre por
    retención (R7): el crudo no vive más que la sesión de depuración, y
    el `check` (R8) dice cuántos hay. El motivo medido (2026-09-07) de
    ambas cosas: un mismo MCP dejó 273 KB de crudos con credenciales en
    tres repos cuyos `.gitignore` no lo cubrían, y nadie sabía dónde.
  - **Bajo HTTP** el servidor no tiene `CLAUDE_PROJECT_DIR` (medido: es
    un contenedor de larga vida que arranca sin relación con ningún
    proyecto; `roots` es un round-trip al cliente con una URI que el
    servidor no tiene montada). Ahí el "proyecto" es el propio servicio:
    `registro_auditoria/` en su directorio de trabajo dentro del
    contenedor, sobre un volumen persistente, con la sesión en cada línea
    (R2, R6) y el proyecto que llamó — si `roots` lo da — como campo de
    la línea. Y como el archivo vive en otra máquina, el MCP expone su
    lectura como herramienta propia (`auditoria`, R9): sin ella nadie del
    lado del cliente lo ve.
  - Una ruta ABSOLUTA en el activador sigue mandando (R4) — es la única
    forma de elegir otro lugar, y es una elección explícita del operador.
  - Si la carpeta no se puede crear, no se escribe y se dice: no hay
    caída a ningún otro lado, porque no escribir tampoco rompe.
- **R2 — Cómo se nombra.** `<mcp>-auditoria[-CRUDA]-<escritor>.jsonl`.
  `<mcp>` derivado del paquete o atado al manifiesto por prueba;
  `<escritor>` = id de sesión en stdio, pid en HTTP.
- **R3 — Qué guarda.** Una línea JSON por llamada: `cuando` (ISO 8601
  UTC), `sesion`, `pid`, `arnes{id, proyecto}`, `cliente`, `herramienta`,
  `argumentos` (lista blanca por forma), `retorno` (su propia lista
  blanca), `resultado` ok|error, `error` (código o tipo del fondo),
  `duracion_ms`, `modo`. En crudo, además: argumentos tal cual y
  respuesta entera con tope de 20 KB, diciendo de cuánto se cortó.
- **R3-bis — Cabecera.** Primera línea del archivo, escrita con la
  primera llamada (no al arrancar). Es donde el registro declara su
  alcance: `tipo:"cabecera"`, versión del esquema de las líneas, quién
  escribe (`mcp` con versión y commit, `pid`, `sesion`, `arnes`,
  `transporte`, `framework` con versión), `modo`, `redaccion{huella,
  valida}` — la huella del `config/auditoria.toml` dice cuáles eran las
  reglas (sin ella, un argumento recortado no se distingue de uno
  completo) y `valida` dice si se aplicaron o si el toml no cargó y se
  está opacando todo; son dos cosas distintas —, `inicio` y `cwd` medido.
  Nada de valores de configuración ni del entorno fuera del catálogo de
  arneses. El `check` (R8) responde "¿cómo está ahora?"; la cabecera
  responde "¿cómo estaba cuando se escribió esto?", que es la pregunta
  que se hace seis meses después, cuando ya no hay a quién llamar.
- **R4 — Activadores y dónde van.** Uno solo: `<MCP>_AUDITORIA` =
  vacío/`0` (apagado) · `1` (redactado) · `crudo` · una ruta ABSOLUTA.
  Solo la ruta absoluta cuenta como ruta; cualquier otro valor APAGA y
  avisa. "Todo lo demás es ruta" resucita R1 por la puerta de atrás: un
  `false` mal escrito crea un directorio `false` en el cwd — el repo de
  otro — y una ruta relativa se resuelve contra ese mismo cwd. La
  asimetría es deliberada: apagado por un typo cuesta un registro que
  falta y se ve en el log; encendido en el lugar equivocado cuesta
  credenciales sueltas. Consecuencia explícita: "crudo en una ruta
  elegida" no se puede expresar, a propósito — el material sensible va
  donde la regla dice. En stdio va
  en el bloque `env` del registro del cliente (`.mcp.json`); en HTTP, en
  el entorno del servicio (compose, unidad). Nunca en un `.env` que un
  script regenera. Las listas blancas van en `config/auditoria.toml` con
  su `.example`: la forma en el repo, nunca un valor.
- **R5 — Compatibilidad: medida o pendiente, nunca prometida.**

  | Caso | Estado | Enganche |
  |---|---|---|
  | Python · fastmcp 4.0.2 y 4.0.3 | medido (gns3, netbox, mtk-chr) | middleware |
  | Python · `mcp` 1.28.1 | medido (mtk-chr antes del port) | override de `call_tool` |
  | Python · `mcp` 2.x | pendiente | middleware nativo |
  | Node · SDK TypeScript | pendiente | paquete hermano, mismo JSONL |
  | stdio | medido | sesión = proceso |
  | streamable-http | medido | `mcp-session-id` en cada línea |

  Las versiones de la tabla son exactas porque lo medido es exacto: el
  paquete y cada MCP pinean con `==` la versión con la que probaron
  (arquitectura-configuracion). Un rango afirma compatibilidad con lo
  que nadie midió; subir de versión es una medición nueva y una fila
  nueva, no un cambio de rango.

- **R6 — Lo pendiente que se implementa deja saber.** Cuando alguien
  aplica la auditoría sobre una casilla pendiente de R5 —otro framework,
  otro transporte, otro lenguaje— o descubre que una medida no vale en
  su caso, el aprendizaje va al saber como ficha (síntoma→acción, con
  `receipt:<hash>`) y la tabla se actualiza en la siguiente versión de
  esta skill. Una casilla no pasa de pendiente a medida por prosa: pasa
  por una ficha con evidencia.
- **R7 — Retención, por proyecto.** Como todo vive en
  `<proyecto>/registro_auditoria/` (R1), limpiar es un solo lugar por
  proyecto: no hay que recordar en qué repos se usó el MCP ni buscar en
  el estado del usuario. El crudo se borra al cerrar la sesión de
  depuración (obligación heredada de logalizar) — y como la carpeta
  puede viajar en un zip o un `COPY .` que ignora el `.gitignore`, ese
  borrado es la protección real del crudo, no un detalle. El redactado
  rota por tamaño o edad. El `check` (R8) cuenta lo que hay en la
  carpeta y avisa cuando hay crudos con más edad que la ventana
  declarada; la herramienta `auditoria` (R9) ofrece `limpiar` para
  hacerlo sin entrar al servidor. Hoy nada limpia solo, y por eso se
  acumulan: la retención automática se declara pendiente hasta que
  alguien la mida en operación.
- **R8 — Bloque `auditoria` del `check`.** Campos fijos, iguales en todo
  MCP: `modo`, `archivo`, `aviso` (solo en crudo), `redaccion`
  (`abierta|cerrada` con el motivo si está cerrada), `acumulado{archivos,
  crudos, bytes, mas_viejo}`. La redacción cerrada — el `toml` que no
  cargó — no rompe nada y sigue escribiendo, pero apaga el tercer camino
  de error sin apagar el registro: `rechazos` devuelve vacío sobre un
  registro con fallos adentro, y el ERROR del arranque es una vez y nadie
  lo mira. Por eso se publica en el `check`. Si contar falla, informa el
  tipo de error y no tumba el `check`.
- **R9 — Lectores estándar en el paquete.** Un formato, unos lectores:
  `cazar` (argumento cuyo valor no vuelve en la respuesta — candidatos,
  no veredictos), `rechazos` (retornos con `rechazadas > 0`),
  `por-sesion`. Sin ellos cada MCP reinventa el `jq`. Bajo HTTP los
  mismos lectores se exponen como herramienta del propio MCP
  (`auditoria`: `estado`, `listar`, `leer` con filtro por sesión,
  herramienta y rango, `cazar`, `rechazos`), porque el archivo vive en el
  servidor. Tres límites que la vuelven segura: solo sirve el REDACTADO —
  el crudo se lee en el servidor, nunca sale por una herramienta a
  cualquier cliente conectado; su propia llamada se anota pero su retorno
  es opaco para el registro (leer el registro no puede escribir el
  registro con el registro adentro); y devuelve páginas con tope
  declarado, diciendo cuántas líneas quedaron afuera (regla 10). Dos
  consecuencias medidas al implementarla: los archivos crudos no se
  listan ni por nombre — una lista con los crudos tachados ya filtra
  cuántas sesiones de depuración hubo y cuándo; y `cazar` por esta vía
  devuelve vacío Y explica por qué (necesita la respuesta entera, que
  solo vive en el crudo): un `[]` a secas se leería como "no hay nada que
  cazar", afirmación que la herramienta no puede hacer. La herramienta
  no se instala sola con el registro: bajo stdio agranda la superficie
  del MCP sin resolver nada; la decide el anfitrión.
- **R10 — Retrofit en tres pasos.** Instalar el paquete; una línea en el
  arranque (`instalar_auditoria(servidor, nombre=…)`, nombre obligatorio,
  enganche elegido por framework detectado); copiar el `.example` y
  medir la superficie para llenarlo. El kit de pruebas del paquete
  (fuga en dos modos, `chdir`, handler registrado, reversión) dice si
  quedó bien. Los tres MCP vivos son los primeros retrofits: la
  extracción se prueba contra ellos antes de llamarse estándar.
- **R11 — El paquete lleva el motor; cada repo lleva sus datos.** Las
  listas blancas, las opacas, las huellas y el catálogo de arneses son
  datos del MCP anfitrión (`config/`), nunca del paquete: si el paquete
  trajera su `redaccion.toml`, el primer MCP que sume una tool con un
  argumento nuevo tendría que tocar el paquete de todos. El descubrimiento
  de arneses se abre desde afuera (entry points o un paquete del
  anfitrión), no iterando los módulos propios del paquete — esa propiedad
  es buena en un repo solo y se da vuelta al compartirse.

- **R12 — Retroalimentación obligatoria, siempre.** Esta skill y su
  paquete se construyeron enteros con lo que devolvieron quienes los
  aplicaron: cada regla de arriba nació de una medición ajena, y tres
  afirmaciones resultaron falsas fuera del repo donde se midieron. Por
  eso quien aplica esta skill —en un MCP nuevo, en un retrofit, o al
  sincronizar una versión— devuelve SIEMPRE una retroalimentación al
  cerrar, no solo cuando algo salió mal. Qué se devuelve: lo que la
  receta no cubría; lo que resultó falso o distinto en este caso, con la
  medición; lo que el paquete no absorbió y hubo que hacer a mano; las
  casillas pendientes que se midieron (R6); y los defectos "forma
  correcta, contenido vacío" encontrados por el camino. A quién: a la
  sesión custodia del catálogo (la que publica esta skill) por mensaje,
  citando commit y recibo; al saber como ficha síntoma→acción con
  `receipt:<hash>` cuando el aprendizaje sirve fuera de este MCP; y al
  paquete como rama o pedido de cambio cuando es código. "Sin novedades"
  también se reporta: es la única forma de saber que la receta se aplicó
  entera y aguantó. Una aplicación que no devuelve nada deja a la skill
  igual que antes y al próximo sin lo que este ya sabe.

## Flujo

1. Medir el contrato del servidor y su reacción al pedido repetido; elegir
   el patrón por descarte medido (regla 1).
2. Medir cuántas sesiones atiende un proceso, el entorno heredado y el
   `cwd` real; acuñar identidad y catalogar el arnés (regla 2).
3. Enganchar el punto único; probarlo contra el handler registrado;
   ejercitarlo con los tres caminos de error (reglas 3 y 4).
4. Medir la superficie de argumentos y retornos; escribir las listas
   blancas por forma, con excepciones motivadas (regla 5).
5. Nombre del archivo, interruptor apagado por omisión, estado visible
   con acumulado del directorio (reglas 6 y 7).
6. Modo crudo con sus cuatro protecciones; suite de fuga en los dos
   modos; E2E contra proceso real; runner verificado (reglas 8 y 9).
7. Cazar en el registro crudo, barrer por forma, declarar alcance y lo
   que queda afuera (reglas 10 y 11).
8. Devolver la retroalimentación a la sesión custodia, al saber y al
   paquete (R12) — también cuando no hubo novedades.

## Referencia viva

Tres implementaciones medidas, en tres combinaciones distintas: repo
`lucky-tool-gns3` (stdio + fastmcp 4; commits `8abbf6f`, `982835c`,
`3a3f8b8`, `01c11a7`, `e42988c`, `4d9088d`, `189a6b4`), repo
`lucky-tool-mtk-chr` (streamable-http; nació sobre SDK `mcp` 1.x y migró
a fastmcp 4 con la misma auditoría — commit `3ccfd57` y su
`docs/retroalimentacion-auditar-mcp.md`, que separa propiedad de
accidente del SDK), repo `lucky-tool-netbox`
(stdio + fastmcp 4, catálogo de arneses; commits `1382090`, `4a6ae47`).
Anclar en
commits, no en rutas. Leer los de gns3 en orden: los que siguen al primero
son huecos aparecidos después de "terminado".

## Salida

```text
PATRON=IDEMPOTENCIA|ASYNC|RECONCILIACION
MEDICION_SERVIDOR=<contrato leído y reacción a repetido>
TRANSPORTE=<stdio|http> SESIONES_POR_PROCESO=<1|N>
IDENTIDAD=<campos acuñados, canal medido, límite declarado>
ENGANCHE=REGISTRADO|BLOCKED
CAMINOS_DE_ERROR=3
REDACCION=WHITELIST_ARGS+WHITELIST_RETORNO+FORMA
ARCHIVO=<mcp>-auditoria[-CRUDA]-…
INTERRUPTOR=OFF_POR_OMISION ESTADO_VISIBLE=SI|NO
TESTS_FUGA=PASS|FAIL RUNNER=PRESENTE|AUSENTE
ALCANCE_DECLARADO=...
RETROALIMENTACION=ENVIADA|SIN_NOVEDADES_ENVIADA|PENDIENTE (<a quién, commit, recibo>)
```

`PENDIENTE` no es un cierre: la aplicación no termina hasta que la
retroalimentación salió.

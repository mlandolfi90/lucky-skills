# lucky-auditoria-mcp

Auditoría interna para un MCP compartido: atribuir cada llamada a su sesión, sin
fugar secretos y sin mentir sobre resultados.

El agujero es estructural, no un descuido. Un MCP típico es una pasarela fina
que se apoya en lo que dice el servidor, y cuando el servidor no atribuye
—credencial única para todas las sesiones, sin logs de acceso— **nadie**
atribuye: el MCP es el único punto donde existe la tripleta
sesión → intención → llamada.

El caso que lo motivó: el 2026-09-04 desaparecieron cuatro proyectos de un
laboratorio y hubo que preguntarle a cada sesión cuál había sido. Salió bien
porque éramos pocos y estábamos despiertos, que no es una garantía.

Lo forense es lo que no tiene reemplazo. Lo que más rinde, en la práctica, es lo
otro: una pasarela sin registro tampoco puede auditarse en su **propia
fidelidad**. Respuestas que afirman más de lo que pasó sólo se ven comparando lo
que entró con lo que salió.

Este paquete es la extracción de la auditoría de `lucky-tool-gns3`, según la
receta R1–R11 de la skill `auditar-mcp` 1.2.2.

## Instalar

```toml
# pyproject.toml del MCP anfitrión
dependencies = [
    "lucky-auditoria-mcp @ git+https://github.com/mlandolfi90/lucky-skills@auditoria-mcp-v0.5.1#subdirectory=packages/lucky-auditoria-mcp",
]
```

## Retrofit en tres pasos

La puerta está abierta: se aplica igual a un MCP nuevo, a uno ya nacido o a uno
copiado. No es requisito de nacimiento.

**1.** Una línea en el arranque, después de registrar las herramientas:

```python
from lucky_auditoria import instalar_auditoria

auditor = instalar_auditoria(
    mcp,
    nombre="gns3-mcp",              # obligatorio
    config="config/auditoria.toml",
    version=__version__,
)
```

`nombre` no tiene default a propósito. Sale del manifiesto del anfitrión
(`[project].name`), nunca de una constante escrita a mano: la skill se aplica
copiando, y una constante copiada hace que dos MCP escriban con el mismo nombre.
Al mover un enganche de subclase a middleware, en el repo original, la
declaración del nombre se cayó y nada falló — el registro escribió
`mcp-sin-nombre-auditoria-…`, forma correcta y origen equivocado.

**2.** El bloque en el `check` que el MCP ya tiene:

```python
{"auditoria": auditor.estado()}
```

Va ahí y no en una herramienta nueva. Una herramienta dedicada a "¿cómo está la
auditoría?" no la llama nadie, que es justo por lo que el problema existía.

**3.** Copiar `config/auditoria.toml.example`, medir la superficie y llenarlo.

Después, heredar el kit de pruebas:

```python
# tests/test_auditoria.py
from lucky_auditoria import Auditor
from lucky_auditoria.pruebas import KitDeAuditoria

class TestAuditoria(KitDeAuditoria):
    def construir(self, tmp_path):
        return Auditor("gns3-mcp", config="config/auditoria.toml")
```

Y en el `conftest.py`, las tres guardas del entorno, que también vienen en el
paquete:

```python
# tests/conftest.py
from pathlib import Path
from lucky_auditoria.pruebas import guardas_del_entorno

globals().update(guardas_del_entorno(Path(__file__).resolve().parents[1]))
```

Hacen tres cosas, y ninguna es higiene:

- **Ningún test hereda un proyecto real.** Claude Code exporta
  `CLAUDE_PROJECT_DIR` al proceso hijo, así que sin esto la suite corre contra
  un repo de verdad en la máquina de quien desarrolla y contra ninguno en el CI:
  el mismo test, dos comportamientos.
- **Ningún test escribe en el `cwd` de pytest**, que bajo HTTP *es* el destino.
  Un test de transporte http que se olvide del `chdir` no falla: escribe en
  `<repo>/registro_auditoria/` y sigue verde.
- **La suite no ensucia la máquina**, comparando los **archivos** de los tres
  lugares prohibidos —estado del usuario, repo del anfitrión, `cwd`— antes y
  después. Se comparan archivos y no si la carpeta existía, porque esa versión
  **se apaga sola en la máquina donde uno ya se ensució**: pasó acá el
  2026-09-07 y lo destapó el CI, con seis celdas en rojo, después de horas en
  verde local.

Vienen en el paquete y no como receta a copiar por el mismo motivo por el que
existe el kit: un modismo que hay que reescribir en cada repo se reescribe mal.

## El interruptor

Uno solo: **`<NOMBRE_DEL_MCP>_AUDITORIA`**.

| Valor | Qué hace |
|---|---|
| vacío o `0` | apagado, de verdad: ni archivo vacío ni directorio creado |
| `1` | redactado, donde dice la tabla de abajo |
| `crudo` | **sin redactar** — ver abajo |
| una ruta **absoluta** | redactado, ahí |
| cualquier otra cosa | **apagado**, y se dice en el log |

Sólo una ruta **absoluta** cuenta como ruta. Un typo o una ruta relativa apagan
el registro en vez de volverse un archivo colgado del `cwd` —que un MCP hereda
de quien lo lanzó, y suele ser el repo de otro. La versión anterior avisaba y
escribía igual, que es la mitad peor de las dos: un aviso que no cambia lo que
pasa no es una protección, es una nota.

Consecuencia deliberada: **"crudo en una ruta elegida" es inexpresable**. Un
valor, una decisión.

Va en el bloque `env` del registro del cliente (`.mcp.json` en stdio) o en el
entorno del servicio (compose, unidad) en HTTP. **Nunca en un `.env` que un
script regenera**: un `.env` reescrito entero desde el gestor de secretos apaga
el interruptor en silencio, y un interruptor que se apaga solo es peor que no
tenerlo.

El modo crudo se enciende con una **palabra**, no con un `1`: encenderlo tiene
que ser un acto deliberado y no el resultado de copiar un ejemplo. Una palabra
que no está en la lista y no parece una ruta **no** se toma como archivo — se
grita por el log. Ese fallback ya costó una sesión entera de depuración
inservible (`crude` se volvió el nombre de un archivo, en modo redactado, en
silencio).

## Dónde escribe

La rama la decide el **transporte**, que es una medición —cuántas sesiones
atiende un proceso— y no una suposición. Elegir mal no da un error: da un
archivo en el lugar equivocado.

| transporte | modo | dónde |
|---|---|---|
| stdio | redactado y crudo | `<proyecto que llamó>/registro_auditoria/` |
| stdio | sin proyecto | **no se escribe**, y se avisa una vez por proceso |
| http | ambos | `./registro_auditoria/` del servicio, en el contenedor |

Una ruta absoluta en la variable manda sobre todo esto —salvo en crudo, que no
se puede pedir por ruta: se pide por palabra, a propósito.

**Una sola carpeta por proyecto, sea cual sea el modo.** Es una decisión del
humano, cerrada: así se ubica por proyecto y se limpia por proyecto, y los
argumentos técnicos se resuelven dentro de ella en vez de moviéndola.

**La carpeta se protege sola**: el paquete escribe adentro un `.gitignore` con
`*` la primera vez que la crea. Así ningún repo que no la esperaba puede
commitearla con un `git add -A`. Ensanchar el `.gitignore` de cada repo arregla
los que uno conoce; la carpeta autoignorada arregla el próximo.

**El crudo comparte carpeta con el redactado desde 0.4.0, y su protección es la
retención.** Hasta 0.3.3 iba al estado del usuario, porque un `.gitignore` lo
respeta git y nadie más: un zip, un `rsync`, un `COPY .` de Docker o un sdist
copian el árbol entero. El precio resultó peor que el riesgo: el crudo quedaba
en un árbol que no es de ningún proyecto, y para borrarlo había que acordarse de
que ese árbol existe. Nadie se acuerda, y el crudo con credenciales es
justamente lo que no puede quedar olvidado. Ahora lo cubre R7: `auditoria
limpiar` borra los crudos del proyecto desde donde uno ya está mirando, y el
`check` dice cuántos hay y de qué edad.

**Sin proyecto no se escribe en ningún lado.** Hasta 0.3.3 caía en
`<estado>/registro_auditoria/_sin_proyecto/`: una carpeta que nadie sabía que
existía, acumulando lo que nadie iba a buscar.

**Bajo HTTP el `cwd` sí se usa, y es lo correcto**: el servidor es un contenedor
de larga vida, su directorio de trabajo es suyo y no lo heredó de ningún
proyecto. Está medido que ahí no hay otra opción: `CLAUDE_PROJECT_DIR` da cero
coincidencias, y `roots` es una petición asíncrona al cliente que depende de que
la declare, hay que cachearla por sesión, y devuelve una URI que el servidor casi
seguro no tiene montada. El proyecto que llamó, si `roots` lo da, va como **campo
de la línea**. Ahí no hay aviso: en stdio la ausencia de proyecto es señal, en
HTTP sería ruido constante, y un aviso que suena siempre deja de leerse.

**Bajo stdio el `cwd` no se usa nunca.** Es lo que el lanzador le dejó al hijo
—medido en `%TEMP%` y en el repo de otro—, no una propiedad del proyecto. El
motivo medido (2026-09-07): un mismo MCP registrado **una** vez dejó 273 KB de
crudos con credenciales en tres repos ajenos, y el `.gitignore` que lo protegía
vivía en su propio repo mientras el archivo caía en cualquier otro.

**Si el directorio no se puede crear, no se escribe en ningún lado.** No
escribir tampoco rompe, porque el escritor ya se traga sus fallos.

`<escritor>` es el id de sesión en stdio (un proceso por sesión) y el pid en
HTTP (N sesiones por proceso: ponerlas en el nombre daría N archivos abiertos
para una colisión que no existe).

## Qué se escribe, y qué no

Lista blanca, siempre. Una lista negra protege lo que uno se acordó de
prohibir; una lista blanca protege lo que uno todavía no inventó.

Un campo es seguro por **nombre + tipo + tope de largo**, no por nombre: el tipo
lo elige el cliente y el registro anota *antes* de que nadie valide, así que
`lineas="<secreto>"` donde se esperaba un entero llega al disco si la lista sólo
mira el nombre. Lo que no coincide con la forma declarada cae a `{tipo, largo}`,
sin valor.

Las listas viven en el `config/auditoria.toml` del **anfitrión**, nunca acá. Si
el paquete trajera las suyas, el primer MCP que sume una herramienta con un
argumento nuevo tendría que tocar el paquete de todos.

El retorno tiene su propia lista, **con el defecto invertido**: un argumento no
declarado se anota reducido a forma (omitirlo dejaría al registro mintiendo
sobre lo que se *pidió*); un retorno no declarado no se anota ni en forma
(anotarlo convertiría el registro en una copia del inventario). Misma palabra,
decisión opuesta según el lado.

Ante cualquier problema de configuración la redacción queda **cerrada** —forma y
ningún valor— y se grita por el log. Es lo opuesto a lo que sale por descuido,
que es una lista escrita y sin efecto.

## Un error tiene tres caminos

| Camino | Cómo llega | Quién lo ve |
|---|---|---|
| La herramienta levanta | excepción | el enganche |
| La herramienta devuelve el error | `error_code` en el retorno | el enganche |
| La herramienta termina bien y el rechazo va adentro | `{fallaron: 3}` | la lista blanca del retorno |

El tercero no tiene señal de protocolo y es el más común: es la forma normal de
cualquier tool por lote. El `is_error` del framework marca **sus** excepciones,
no los rechazos de la pasarela — creerle anota `ok` sobre el 100% de los
rechazos.

Del error se anota el **tipo o el código**, jamás el mensaje, que arrastra los
argumentos. Y se busca al fondo de la cadena: fastmcp 4 envuelve todo en
`ToolError`, así que sin recorrer `__cause__` los quince fallos distintos se
anotan igual. El envoltorio se guarda aparte cuando difiere, porque `ToolError`
sobre `NodeNotFound` dice "el dominio lo rechazó" y un `ValidationError` pelado
dice "faltó un argumento".

## Modo crudo

Para depurar hace falta ver el argumento mandado **y** la respuesta entera en la
misma línea: separados no se cruzan. Un "casi crudo" que redacta un poco no
sirve y da falsa seguridad — o redacta, o no.

El precio es que el archivo pasa a ser material sensible. Por eso: se enciende
con una palabra, el archivo se llama `…-CRUDA-…` a gritos, cada línea lleva
`"modo": "crudo"` (la marca viaja con el contenido, por si alguien pega una
línea suelta en otro lado), y hay un WARNING al primer uso.

Como ese WARNING es una vez por proceso y nadie mira el log, lo que de verdad lo
recuerda es el **acumulado** del `estado()`. Medido: once archivos crudos y
44 KB en un día sin que nadie lo notara, horas después de borrar quince.

Es el punto donde auditar se vuelve *logalizar* y hereda sus obligaciones:
temporal, con fecha de apagado, se borra al terminar.

## Leer el registro

Bajo **stdio** el archivo está en el disco del que llamó, y el CLI alcanza:

```bash
lucky-auditoria por-sesion  <proyecto>/registro_auditoria/*.jsonl
lucky-auditoria rechazos    ...
lucky-auditoria cazar       <estado>/registro_auditoria/<proyecto>/*CRUDA*.jsonl
```

`cazar` es la que paga el paquete: "argumento que el cliente mandó y cuyo valor
no aparece en ningún escalar de la respuesta", comparando por **valor** y no por
substring (buscar `str(1)` da verdadero contra cualquier `1` suelto, y la señal
se vuelve inútil para enteros). Se saltean `None` y los booleanos —un booleano no
"vuelve", cambia el camino— y no corre sobre rechazos, donde es normal que el
argumento no haya tenido efecto.

`afirmaciones` es la otra mitad, medida por `lucky-tool-mtk-chr` sobre 39 verbos:
**éxito con efecto vacío** (`ok: true` con todas las listas vacías — todas, no
algunas: una vacía entre cinco llenas es normal) y **respuesta flaca** (`ok:
true` con dos claves o menos, umbral absoluto). Encontró tres defectos de "no
fallaba, contestaba mal": una duración afirmada de 24 h contra un timeout real
de 59m58s, un conteo sobre una ventana truncada sin decirlo, y 20 de 200
coincidencias sin decirlo. Los tres se arreglaron **reportando** lo que pasaba,
nunca cambiando el comportamiento. Produce **candidatos, nunca veredictos** — hay argumentos que
legítimamente no vuelven, y decidirlo exigiría conocer cada verbo. Se tría a
mano. Un hallazgo no se cierra arreglando el caso: se convierte en una forma que
se barre en todo el repo.

Bajo **HTTP** el archivo vive dentro del contenedor, así que sin una herramienta
que lo exponga nadie del lado del cliente lo ve. El paquete la trae:

```python
from lucky_auditoria import herramienta
herramienta.instalar(mcp, auditor)      # solo tiene sentido bajo HTTP
```

`auditoria(action=...)` con `estado`, `listar`, `leer` (filtros `sesion`,
`herramienta`, `desde`, `hasta`, `limite`, `salteo`), `cazar`, `rechazos` y
`por_sesion`.

**Tres límites la vuelven segura**, porque exponerla la pone al alcance de
cualquier cliente conectado:

1. **Sólo el redactado.** El crudo se lee en el servidor y no sale por una
   herramienta jamás. Los archivos crudos no se listan ni por nombre — decir
   "hay tres que no te muestro" ya cuenta cuántas sesiones de depuración hubo. Y
   si una línea suelta dice `modo: crudo`, se descarta **y se dice cuántas**.
2. **Su retorno es opaco para el registro.** La llamada se anota —quién leyó el
   registro es información forense de primera— pero su retorno no: la segunda
   lectura traería la primera, y a la tercera el archivo crece con copias de sí
   mismo. Lo decide el paquete, no el `config` del anfitrión: no es un dato
   suyo, es una propiedad de esta herramienta, y quien se olvide de declararla
   se lleva la recursión puesta.
3. **Pagina con tope declarado**, diciendo cuántas líneas quedaron afuera. Un
   lector que recorta en silencio comete la familia de defectos que este
   registro vino a cazar.

`cazar` por esta vía devuelve siempre vacío **y explica por qué**: necesita la
respuesta entera, que sólo existe en el crudo. Un `[]` a secas se leería como
"no hay nada que cazar", y eso esta herramienta no lo puede afirmar.

## Una fuga que este paquete NO cubre

**El log del framework escribe el valor que la lista blanca tachó.** Medido con
fastmcp 4.0.3, sin buscarlo: ante un argumento con el tipo equivocado, fastmcp
loguea `Invalid arguments for tool 'x': [{... 'input': '<el valor entero>'}]` en
un WARNING propio. O sea que el `Sup3rS3cr3t0` que el registro guardó como
`{tipo: str, largo: 12}` sale íntegro por el log del proceso.

El paquete no puede arreglarlo: es el log del framework, no el nuestro. Lo que
hace es no dejar que pase inadvertido — hay un test que lo afirma, y el día que
fastmcp deje de hacerlo se pone rojo y este aviso sobra.

Mientras tanto: **el log del proceso de un MCP auditado es material sensible
aunque el registro no lo sea.** Vale lo mismo que ya se sabía de uvicorn
logueando `?token=<JWT>` en claro.

## Compatibilidad

| Caso | Estado | Enganche |
|---|---|---|
| Python · **fastmcp 4.0.3** (con `mcp` 2.1.1) | medido: suite propia, y en repos vivos con 4.0.2 | `add_middleware` |
| Python · `mcp` 1.x | **pendiente** | `request_handlers[CallToolRequest]` |
| Python · `mcp` 2.x | pendiente | middleware nativo |
| Node · SDK TypeScript | pendiente | paquete hermano, mismo JSONL |
| stdio | medido en **Python 3.12.10** | sesión = proceso |
| streamable-http | escrito; **medición pendiente** en un servidor vivo | `mcp-session-id` en cada línea |

Las versiones de la tabla son exactas a propósito, y las del `pyproject.toml` están
pineadas con `==`: un rango afirma compatibilidad con versiones que nadie probó,
incluidas las que todavía no existen. Las versiones del `pyproject.toml` están pineadas con `==`: un rango afirma
compatibilidad con versiones que nadie probó, incluidas las que todavía no
existen. A mano, la suite corrió sólo en **Python 3.12.10**, en dos venv
distintos de la misma máquina — que no son dos entornos. Lo demás lo mide el CI
(`.github/workflows/auditoria-mcp.yml`), y hay que **leerlo**:
`gh run list --workflow auditoria-mcp.yml`.

Estado al 2026-09-07, leído de los runs: **3.10, 3.12 y 3.13 en verde**, en
`ubuntu-latest` y `windows-latest`.

Este párrafo se corrigió dos veces, en direcciones opuestas, y las dos quedan
escritas porque son la razón de la regla:

1. Dijo que **3.13 estaba medida a mano**. Falso: lo dio por sentado una sesión,
   se copió sin verificar, y quedó en dos repos con forma de medición.
2. Después dijo que **el CI no se había ejecutado nunca**. También falso: había
   corrido doce veces, las tres últimas en **rojo**, y ninguna de las dos
   sesiones había mirado los runs. El test que rompía era el escrito para medir
   3.10, que importaba `tomllib` — el módulo que en 3.10 no existe. El único
   test que medía el respaldo era el que no podía correr donde el respaldo se
   usa.

De ahí la forma: **exigir que exista un runner no alcanza; hay que leer su
resultado.** Un CI rojo que nadie mira vale lo mismo que uno que no corre, con
el agravante de que parece cobertura.

El enganche de `mcp` 1.x está **escrito y no medido**: el override que sí se
midió es el de otro repo, sobre `@server.call_tool()`; el de acá envuelve el
handler de la tabla de ruteo, que es la propiedad correcta pero no es el mismo
código. Una casilla no pasa de pendiente a medida por prosa: pasa por una ficha
con evidencia.

## Lo que este paquete no hace, y se dice

Forense y depuración, **no defensa**. La otra mitad es identidad propia contra el
servidor —usuarios y ACL por espacio de trabajo en vez de credencial
compartida—: con eso, cerrar el laboratorio de otro sería un 403 y no un
incidente. Esto responde "quién y qué quiso hacer"; aquello responde "y además
no lo dejó".

Y el registro declara su propio alcance, incluido lo que **no** ve: encuentra
defectos en el borde de una llamada. Lo que el MCP *declara* —el texto de
instrucciones, las descripciones de herramientas— no lo ve, porque nadie llama a
una descripción. Esa prosa es superficie aparte, y se verifica contra el runtime
(`list_tools()`), nunca contra otro texto.

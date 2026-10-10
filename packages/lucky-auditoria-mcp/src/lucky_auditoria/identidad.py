"""Quien es este proceso, para poder atribuirle lo que hace.

El transporte decide cuantas sesiones atiende un proceso, y de ahi sale todo lo
demas. Bajo `stdio` el cliente levanta UN proceso por sesion -el stdin/stdout lo
creo quien lanzo, y dos clientes no pueden compartirlo-, asi que el proceso YA
ES la sesion y solo faltaba nombrarla. Bajo `streamable-http` un proceso atiende
N sesiones y el id viaja en el protocolo (`mcp-session-id`): ahi no hay que
acuñar nada.

## Lo que NO sirve, medido

- El `session_id` del framework: fastmcp 4 bajo stdio reconstruye la conexion
  por pedido, asi que da un UUID nuevo en cada llamada. Es el campo que uno
  agarra primero y el que no sirve.
- El nombre del cliente: `claude-code` en todas las sesiones abiertas a la vez.
  Nombra al producto.
- El `cwd`: hay lanzadores que lo ponen en `%TEMP%` para todos los espacios de
  trabajo. A veces nombra el repo y a veces no nombra nada, y no se puede saber
  cual de las dos sin mirar.

Lo que si llega es el entorno heredado del arnes, y eso lo resuelve
`arneses.py`. Cuando el arnes trae un id de sesion, ese manda: es el id exacto
de la conversacion, y correlaciona el registro con lo que el humano ve. Cuando
no, se acuña uno aca, que es el unico componente 1:1 con la sesion que uno
controla.
"""

import contextvars
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from lucky_auditoria import arneses

_ACUÑADO = uuid.uuid4().hex[:12]
_INICIADA_EN = datetime.now(timezone.utc).isoformat()
_CLIENTE: dict[str, Any] = {}
# Por llamada, no por proceso: bajo HTTP dos sesiones se atienden a la vez y una
# global del modulo se pisa entre la anotacion y el `await` de la herramienta,
# con lo que la linea sale con el id de la sesion equivocada (medido por
# lucky-tool-mtk-chr sobre 0.8.0, ficha CAP-7824fd652563). Un ContextVar viaja
# con la tarea que atiende ESA llamada y no con el proceso.
_SESION_DEL_TRANSPORTE: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "lucky_auditoria_sesion_del_transporte", default=None
)
# El cliente de ESTA llamada, por el mismo motivo que la sesion (P, pedido de
# lucky-tool-mtk-chr el 2026-10-05): bajo HTTP `_CLIENTE` es del proceso, y
# todas las sesiones salian con el nombre del primer cliente que llamo.
_CLIENTE_DE_LA_LLAMADA: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "lucky_auditoria_cliente_de_la_llamada", default=None
)
_RAIZ_DEL_PROYECTO: str | None = None

# Lo que puede ir en un nombre de archivo sin sorpresas en ningun sistema.
_NOMBRE_SEGURO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def anotar_cliente(
    nombre: str | None, version: str | None = None, *, declara_roots: bool = False
) -> None:
    """Como se presento el cliente en el handshake. Informativo, no identifica.

    Sin esto la sesion sigue teniendo su id: por eso se puede llamar tarde, una
    vez, desde el enganche, y por eso no importa si nunca llega.
    """
    if nombre:
        _CLIENTE["name"] = nombre
    if version:
        _CLIENTE["version"] = version
    if declara_roots:
        _CLIENTE["declara_roots"] = True


def anotar_cliente_de_la_llamada(
    nombre: str | None, version: str | None = None, *, declara_roots: bool = False
) -> contextvars.Token:
    """El cliente que hizo ESTA llamada, bajo HTTP. Se suelta al terminar.

    Bajo stdio no hace falta -un proceso, un cliente- y alcanza con
    `anotar_cliente`. Bajo HTTP cada sesion trae el suyo, y una global del
    proceso le ponia a todas el nombre de la primera.
    """
    cliente: dict[str, Any] = {}
    if nombre:
        cliente["name"] = nombre
    if version:
        cliente["version"] = version
    if declara_roots:
        cliente["declara_roots"] = True
    return _CLIENTE_DE_LA_LLAMADA.set(cliente or None)


def olvidar_cliente_de_la_llamada(marca: contextvars.Token) -> None:
    """Deshace la anotacion de esa llamada. Nunca levanta."""
    try:
        _CLIENTE_DE_LA_LLAMADA.reset(marca)
    except (ValueError, RuntimeError):
        pass


def anotar_raiz_del_proyecto(ruta: str | None) -> None:
    """La raiz que el cliente declaro por `roots`, cuando el arnes no la dio.

    Es para stdio, donde R1 la usa para saber EN QUE CARPETA escribir. Bajo HTTP
    no se usa: ahi lo que el cliente declara va a la linea de apertura como
    dicho (R1-bis), nunca como `proyecto` a secas. El paquete no la llama solo;
    la llama el anfitrion que tiene los `roots` a mano.
    """
    global _RAIZ_DEL_PROYECTO
    _RAIZ_DEL_PROYECTO = ruta or None


def raiz_del_proyecto() -> str | None:
    """Que espacio de trabajo llamo, por orden de confianza. Nunca el cwd.

    El cwd es lo que el lanzador le dejo al hijo -medido: `%TEMP%`, o el repo de
    otro-, no una propiedad del proyecto. Si no hay ninguna de las dos fuentes,
    se devuelve None y el que llama decide: no se adivina.
    """
    del_arnes = arneses.detectar().get("proyecto")
    return del_arnes or _RAIZ_DEL_PROYECTO


def anotar_sesion_del_transporte(identificador: str | None) -> contextvars.Token:
    """El `mcp-session-id` de HTTP, que manda sobre todo lo demas.

    Es el unico caso donde la sesion NO es el proceso: un servidor HTTP atiende
    varias, y el id tiene que cambiar por llamada. El enganche lo pone antes de
    registrar, para ESA llamada, y lo suelta con `olvidar_sesion_del_transporte`
    al terminar. Hasta 0.8.0 esta funcion existia y nadie la llamaba: todas las
    sesiones HTTP salian con el id del proceso.
    """
    return _SESION_DEL_TRANSPORTE.set(identificador or None)


def olvidar_sesion_del_transporte(marca: contextvars.Token) -> None:
    """Deshace la anotacion de esa llamada. Nunca levanta."""
    try:
        _SESION_DEL_TRANSPORTE.reset(marca)
    except (ValueError, RuntimeError):
        pass


def id_de_sesion() -> str:
    """El id que se escribe en cada linea, por orden de confianza."""
    del_transporte = _SESION_DEL_TRANSPORTE.get()
    if del_transporte:
        return del_transporte
    heredado = arneses.detectar().get("sesion")
    return heredado or _ACUÑADO


def get_sesion() -> dict[str, Any]:
    """Quien es este proceso. `pid` va aparte del `id` a proposito.

    El id sobrevive en los registros escritos; el pid sirve para encontrar el
    proceso vivo ahora mismo. Son dos preguntas distintas.
    """
    return {
        "id": id_de_sesion(),
        "pid": os.getpid(),
        "iniciada": _INICIADA_EN,
        # Se informa porque a veces es el dato -y cuesta cero-, pero no se usa
        # para decidir nada: ver el encabezado del modulo.
        "cwd": os.getcwd(),
        # El proyecto que llamo va en la LINEA siempre, venga del arnes o de
        # los `roots` del protocolo. Bajo HTTP es el unico lugar donde puede
        # ir: la carpeta es del servidor, que no es de ningun proyecto.
        "arnes": {**arneses.detectar(), "proyecto": raiz_del_proyecto()},
        "cliente": _CLIENTE_DE_LA_LLAMADA.get() or dict(_CLIENTE) or None,
    }


def escritor(transporte: str | None = None) -> str:
    """Quien firma el ARCHIVO, que no es siempre quien firma la linea.

    Bajo stdio, sesion == proceso y el id de sesion nombra bien al archivo. Bajo
    HTTP hay N sesiones por proceso: ponerlas en el nombre daria N archivos
    abiertos para una colision que no existe, porque el candado de hilos ya
    ordena a los escritores de un proceso. Ahi firma el pid.

    Lo decide el TRANSPORTE que declaro el anfitrion (U). Hasta 0.9.0 lo decidia
    `if _SESION_DEL_TRANSPORTE:`, que pregunta por el objeto `ContextVar` -y un
    objeto siempre es verdadero- en vez de por su valor: bajo stdio todo
    archivo salia firmado con el pid, contra R2. Sin transporte declarado se
    mira el VALOR de la sesion de esta llamada.

    El id de sesion va al nombre solo si sirve de nombre (S-19): viene del
    entorno, y con un separador `Path.with_name` levantaba. Si no sirve, firma
    el acuñado; la linea sigue llevando el id tal cual.
    """
    if transporte is not None:
        http = transporte != "stdio"
    else:
        http = _SESION_DEL_TRANSPORTE.get() is not None
    if http:
        return f"pid{os.getpid()}"
    sesion = id_de_sesion()
    if _NOMBRE_SEGURO.fullmatch(sesion):
        return sesion
    return _ACUÑADO

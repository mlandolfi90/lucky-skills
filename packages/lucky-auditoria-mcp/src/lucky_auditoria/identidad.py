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

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from lucky_auditoria import arneses

_ACUÑADO = uuid.uuid4().hex[:12]
_INICIADA_EN = datetime.now(timezone.utc).isoformat()
_CLIENTE: dict[str, Any] = {}
_SESION_DEL_TRANSPORTE: str | None = None
_RAIZ_DEL_PROYECTO: str | None = None


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


def anotar_raiz_del_proyecto(ruta: str | None) -> None:
    """La raiz que el cliente declaro por `roots`, cuando el arnes no la dio.

    La pide el ENGANCHE, que es el que tiene la sesion a mano, y no este modulo:
    preguntar por el protocolo es una llamada al cliente, y la identidad tiene
    que poder responderse sin red. Se anota una vez y queda.
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


def anotar_sesion_del_transporte(identificador: str | None) -> None:
    """El `mcp-session-id` de HTTP, que manda sobre todo lo demas.

    Es el unico caso donde la sesion NO es el proceso: un servidor HTTP atiende
    varias, y el id tiene que cambiar por llamada. El enganche lo pone antes de
    registrar.
    """
    global _SESION_DEL_TRANSPORTE
    _SESION_DEL_TRANSPORTE = identificador or None


def id_de_sesion() -> str:
    """El id que se escribe en cada linea, por orden de confianza."""
    if _SESION_DEL_TRANSPORTE:
        return _SESION_DEL_TRANSPORTE
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
        "cliente": dict(_CLIENTE) or None,
    }


def escritor() -> str:
    """Quien firma el ARCHIVO, que no es siempre quien firma la linea.

    Bajo stdio, sesion == proceso y el id de sesion nombra bien al archivo. Bajo
    HTTP hay N sesiones por proceso: ponerlas en el nombre daria N archivos
    abiertos para una colision que no existe, porque el candado de hilos ya
    ordena a los escritores de un proceso. Ahi firma el pid.
    """
    if _SESION_DEL_TRANSPORTE:
        return f"pid{os.getpid()}"
    return id_de_sesion()

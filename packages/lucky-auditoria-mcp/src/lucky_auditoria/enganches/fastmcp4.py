"""Enganche para fastmcp 4: un middleware, no un decorador por herramienta.

Decorar herramienta por herramienta hace que la N+1 nazca sin auditar, y nadie
se entera: sacar una linea no rompe nada visible. Por el middleware, una
herramienta nueva queda auditada por nacer.

## De donde sale el nombre del cliente, y por que NO por `on_initialize`

El protocolo MCP tiene un handshake donde el cliente se presenta, y fastmcp
declara un gancho `on_initialize` para verlo. **En 4.0.2 ese gancho no dispara**
-medido el 2026-09-04 en aislamiento, con un servidor de dos lineas: sobre la
misma sesion, `on_call_tool` se ejecuta y `on_initialize` nunca. Un gancho
declarado no es un gancho que corre.

El dato igual esta, un nivel mas adentro y en snake_case: lo guarda la sesion en
`session.client_params.client_info`, desde la primera llamada a una herramienta.
Dos veces se lo busco en `clientInfo` -el nombre que usa el protocolo por el
cable- y las dos salio `cliente: null` sin que nada fallara: forma correcta y
contenido vacio, que es el bicho de la casa.
"""

import json
import time
from typing import Any

from fastmcp.server.middleware import Middleware

from lucky_auditoria import identidad
from lucky_auditoria.rechazos import codigo_de_error
from lucky_auditoria.registro import Auditor, tipo_del_error


def _cliente_de_la_sesion(contexto: Any) -> tuple:
    """Como se presento el cliente, sin asumir la forma del envoltorio.

    Todo con `getattr` y dentro de un `try`: si el cliente no se presenta, o
    fastmcp mueve el campo, devuelve None y la sesion sigue teniendo su id.
    Auditar no puede romper una llamada.
    """
    try:
        sesion = getattr(getattr(contexto, "fastmcp_context", None), "session", None)
        params = getattr(sesion, "client_params", None)
        info = getattr(params, "client_info", None) or getattr(params, "clientInfo", None)
        if info is None:
            return None, None, False
        # `roots` es la capacidad del protocolo para preguntarle al cliente cual
        # es su espacio de trabajo. Medido el 2026-09-04: claude-code 2.1.259 SI
        # la declara, asi que ese camino existe si algun dia hace falta.
        capacidades = getattr(params, "capabilities", None)
        declara_roots = getattr(capacidades, "roots", None) is not None
        return getattr(info, "name", None), getattr(info, "version", None), declara_roots
    except Exception:
        return None, None, False


def _texto_de(resultado: Any) -> str | None:
    """El texto que devolvio la herramienta."""
    try:
        partes = [getattr(b, "text", None) for b in (getattr(resultado, "content", None) or [])]
        texto = "".join(p for p in partes if p)
        return texto or None
    except Exception:
        return None


def _datos_de(texto: str | None) -> Any:
    """El retorno parseado, para que los conteos salgan de datos y no de texto.

    Parsear, no buscar la palabra: un texto que MENCIONA `error_code` no es un
    fallo, y un `grep` no sabe la diferencia.
    """
    if not texto or "{" not in texto:
        return None
    try:
        return json.loads(texto)
    except (ValueError, TypeError):
        return None


def _codigo_de_error(datos: Any) -> str | None:
    """El codigo si la herramienta DEVOLVIO un error en vez de levantarlo.

    Medido: un `node create` con `NODE_NAME_TAKEN` quedaba como
    `resultado: "ok"`. Las formas que se reconocen y por que viven en
    `rechazos.py`, compartido con el enganche de mcp 1.x.
    """
    return codigo_de_error(datos)


def _sesion_del_transporte(contexto: Any) -> str | None:
    """El `mcp-session-id` con el que el cliente hizo ESTA llamada.

    Solo vale bajo HTTP: el servidor lo acuña en el `initialize` y el cliente
    lo devuelve en cada pedido, y es lo unico que distingue a los N clientes
    que atiende un mismo proceso. Se lee del pedido -la cabecera, o el id que
    el SDK ya le puso a la conexion-, y NO de `Context.session_id`: medido con
    fastmcp 4.0.3, esa propiedad inventa un UUID nuevo por pedido cuando la
    cabecera falta (y bajo stdio o en memoria siempre falta), con lo que cada
    llamada saldria como una sesion distinta, peor que el id del proceso. Sin
    cabecera se devuelve None y la sesion sigue siendo el proceso. Todo con
    `getattr`: auditar no puede romper una llamada.
    """
    try:
        fastmcp_context = getattr(contexto, "fastmcp_context", None)
        conexion = getattr(getattr(fastmcp_context, "session", None), "_connection", None)
        del_sdk = getattr(conexion, "session_id", None)
        if del_sdk:
            return str(del_sdk)
        pedido = getattr(getattr(fastmcp_context, "request_context", None), "request", None)
        cabeceras = getattr(pedido, "headers", None)
        if cabeceras is None:
            return None
        return cabeceras.get("mcp-session-id") or None
    except Exception:
        return None


class AuditoriaMiddleware(Middleware):
    """Anota que sesion llamo a que herramienta, con que resultado."""

    def __init__(self, auditor: Auditor) -> None:
        if not isinstance(auditor, Auditor):
            # Un middleware sin auditor -y por lo tanto sin nombre- no se puede
            # construir. Es la leccion de la mudanza de enganche: la declaracion
            # del nombre se cayo y nada fallo.
            raise TypeError("AuditoriaMiddleware necesita un Auditor construido")
        self.auditor = auditor
        self._cliente_anotado = False

    def _anotar_cliente_una_vez(self, contexto: Any) -> None:
        if self._cliente_anotado:
            return
        nombre, version, declara_roots = _cliente_de_la_sesion(contexto)
        if nombre or version:
            identidad.anotar_cliente(nombre, version, declara_roots=declara_roots)
        # Se marca igual aunque no haya venido nada: reintentarlo en cada llamada
        # seria pagar un getattr por llamada para el mismo None.
        self._cliente_anotado = True

    async def on_call_tool(self, context, call_next):
        # Bajo HTTP el id es de la sesion que hizo ESTA llamada y se anota en
        # el contexto de la tarea que la atiende, no en el proceso: dos
        # clientes concurrentes no se pisan. Se suelta pase lo que pase.
        marca = None
        if self.auditor.transporte != "stdio":
            marca = identidad.anotar_sesion_del_transporte(_sesion_del_transporte(context))
        try:
            return await self._auditar_llamada(context, call_next)
        finally:
            if marca is not None:
                identidad.olvidar_sesion_del_transporte(marca)

    async def _auditar_llamada(self, context, call_next):
        self._anotar_cliente_una_vez(context)
        params = getattr(context, "message", None)
        herramienta = getattr(params, "name", "?")
        argumentos = getattr(params, "arguments", None)
        comenzo = time.monotonic()
        try:
            resultado = await call_next(context)
        except Exception as error:
            real, envoltorio = tipo_del_error(error)
            self.auditor.registrar(
                herramienta,
                argumentos,
                resultado="error",
                duracion_ms=int((time.monotonic() - comenzo) * 1000),
                # El tipo, no el mensaje: el texto de una excepcion puede
                # arrastrar lo que se le paso a la herramienta.
                error=real,
                envoltorio=envoltorio,
            )
            # Se re-lanza sin envolver: el enganche no puede cambiar lo que el
            # modelo recibe.
            raise
        texto = _texto_de(resultado)
        datos = _datos_de(texto)
        codigo = _codigo_de_error(datos)
        self.auditor.registrar(
            herramienta,
            argumentos,
            resultado="error" if codigo else "ok",
            duracion_ms=int((time.monotonic() - comenzo) * 1000),
            error=codigo,
            # El tercer camino: la herramienta termina bien y el rechazo va
            # adentro. El resumen queda al lado del estado -el estado habla de
            # la llamada, el resumen de cada item.
            retorno=self.auditor.redaccion.retorno_de(datos),
            respuesta=texto if self.auditor.modo() == "crudo" else None,
        )
        return resultado


def instalar(servidor: Any, auditor: Auditor) -> Any:
    """Suma el middleware al servidor y devuelve el auditor."""
    servidor.add_middleware(AuditoriaMiddleware(auditor))
    return auditor

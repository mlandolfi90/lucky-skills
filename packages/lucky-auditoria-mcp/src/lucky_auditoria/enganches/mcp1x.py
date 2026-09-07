"""Enganche para el SDK `mcp` 1.x, que no tiene middleware.

La propiedad que sobrevive a los SDK no es "el middleware del framework" sino
"el punto por donde pasa todo `tools/call`". En `mcp` 1.x ese punto es la
entrada de `CallToolRequest` en la TABLA DE RUTEO del servidor, asi que se
envuelve ahi y no en el decorador `@server.call_tool()`: envolver el decorador
audita lo que uno registro, envolver la tabla audita lo que el servidor va a
ejecutar de verdad, que es lo que importa cuando el SDK cambia como los liga.

## Estado de esta casilla

El enganche por override de `call_tool` esta medido en un MCP real (mtk-chr,
antes de su port a fastmcp). Esta version generica, contra la tabla de ruteo, NO
esta medida todavia contra un servidor `mcp` 1.x vivo: se escribio portando la
propiedad, no copiando aquel codigo. Hasta que alguien la ejercite y lo anote,
se declara pendiente. Una casilla no pasa de pendiente a medida por prosa.
"""

import time
from typing import Any

from lucky_auditoria.registro import Auditor, tipo_del_error


def _texto_de(resultado: Any) -> str | None:
    """El texto del resultado, sin asumir en que forma viene envuelto."""
    try:
        contenido = resultado
        for atributo in ("root", "content"):
            adentro = getattr(contenido, atributo, None)
            if adentro is not None:
                contenido = adentro
        if isinstance(contenido, str):
            return contenido or None
        partes = [getattr(b, "text", None) for b in (contenido or [])]
        texto = "".join(p for p in partes if p)
        return texto or None
    except Exception:
        return None


def instalar(servidor: Any, auditor: Auditor) -> Auditor:
    """Envuelve el handler REGISTRADO de `tools/call`. Idempotente.

    Idempotente a proposito: instalar dos veces por descuido duplicaria cada
    linea del registro, y un registro con todo dos veces miente sobre el conteo
    de llamadas, que es lo primero que alguien mira.
    """
    from mcp.types import CallToolRequest

    tabla = servidor.request_handlers
    original = tabla.get(CallToolRequest)
    if original is None:
        raise RuntimeError(
            "lucky-auditoria: el servidor no tiene registrado un handler de "
            "`tools/call`. Instalar la auditoria DESPUES de registrar las "
            "herramientas."
        )
    if getattr(original, "_lucky_auditoria", False):
        return auditor

    async def auditado(peticion):
        params = getattr(peticion, "params", None)
        herramienta = getattr(params, "name", "?")
        argumentos = getattr(params, "arguments", None)
        comenzo = time.monotonic()
        try:
            resultado = await original(peticion)
        except Exception as error:
            real, envoltorio = tipo_del_error(error)
            auditor.registrar(
                herramienta,
                argumentos,
                resultado="error",
                duracion_ms=int((time.monotonic() - comenzo) * 1000),
                error=real,
                envoltorio=envoltorio,
            )
            raise
        texto = _texto_de(resultado)
        datos = None
        if texto and "{" in texto:
            import json

            try:
                datos = json.loads(texto)
            except (ValueError, TypeError):
                datos = None
        # En 1.x el propio SDK marca el error devuelto en `isError`, y ademas
        # vale el codigo del dominio: los dos son el mismo camino segundo.
        codigo = None
        if isinstance(datos, dict) and datos.get("error_code"):
            codigo = str(datos["error_code"])
        elif getattr(getattr(resultado, "root", resultado), "isError", False):
            codigo = "IS_ERROR"
        auditor.registrar(
            herramienta,
            argumentos,
            resultado="error" if codigo else "ok",
            duracion_ms=int((time.monotonic() - comenzo) * 1000),
            error=codigo,
            retorno=auditor.redaccion.retorno_de(datos),
            respuesta=texto if auditor.modo() == "crudo" else None,
        )
        return resultado

    auditado._lucky_auditoria = True
    tabla[CallToolRequest] = auditado
    return auditor

"""Elegir el enganche por el framework que el servidor ES, no por lo que diga.

Conviven bases incompatibles -`mcp` 1.x sin middleware, `mcp` 2.x con
middleware, `fastmcp` 4.x con hooks- y la deteccion mira la CAPACIDAD del objeto
(`add_middleware`, `request_handlers`), no el nombre del paquete: un servidor
envuelto por el anfitrion sigue teniendo la capacidad y pierde el nombre.
"""

from typing import Any


def detectar(servidor: Any) -> str:
    """`fastmcp4`, `mcp1x`, o levanta diciendo que se encontro."""
    if hasattr(servidor, "add_middleware"):
        return "fastmcp4"
    if hasattr(servidor, "request_handlers"):
        return "mcp1x"
    raise TypeError(
        "lucky-auditoria: no se reconoce el framework de "
        f"{type(servidor).__module__}.{type(servidor).__name__}. Los enganches "
        "conocidos son fastmcp 4 (`add_middleware`) y mcp 1.x "
        "(`request_handlers`). Pasar `enganche=` a mano si es otro."
    )

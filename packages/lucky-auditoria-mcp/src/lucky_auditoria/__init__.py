"""Auditoria interna para un MCP compartido: quien hizo que, de este lado.

El agujero es estructural y no un descuido. Un MCP tipico es una pasarela fina
que se apoya en lo que dice el servidor, y cuando el servidor no atribuye
-credencial unica para todas las sesiones, sin logs de acceso- nadie atribuye:
el MCP es el unico punto donde existe la tripleta sesion -> intencion ->
llamada. El caso que lo motivo: el 2026-09-04 desaparecieron cuatro proyectos de
un lab y hubo que preguntarle a cada sesion. Salio bien porque eramos pocos y
estabamos despiertos, que no es una garantia.

Y hay una segunda mitad que rinde mas todavia: una pasarela sin registro tampoco
puede auditarse en su propia fidelidad. Respuestas que afirman mas de lo que
paso solo se ven comparando lo que entro con lo que salio.

## El uso

    from lucky_auditoria import instalar_auditoria

    auditor = instalar_auditoria(mcp, nombre="gns3-mcp", config="config/auditoria.toml")

y en el `check` que el MCP ya tiene:

    {"auditoria": auditor.estado()}

`nombre` es obligatorio. Sale del manifiesto del anfitrion, nunca de una
constante escrita a mano: la skill se aplica copiando, y una constante copiada
hace que dos MCP escriban con el mismo nombre.

## Lo que este paquete NO trae

Las listas blancas, las herramientas opacas, las huellas y los arneses son datos
del MCP anfitrion y viven en su `config/`. Si el paquete trajera su
`redaccion.toml`, el primer MCP que sume una herramienta con un argumento nuevo
tendria que tocar el paquete de todos.

Tampoco trae defensa: esto es forense y depuracion. La otra mitad es identidad
propia contra el servidor -usuarios y ACL por espacio de trabajo en vez de
credencial compartida-, y con eso cerrar el laboratorio de otro seria un 403 y
no un incidente. Esto responde "quien y que quiso hacer"; aquello responde "y
ademas no lo dejo".
"""

from typing import Any

from lucky_auditoria import arneses, enganches, identidad, lectores, redaccion
from lucky_auditoria.arneses import Arnes
from lucky_auditoria.registro import Auditor, tipo_del_error

__all__ = [
    "Arnes",
    "Auditor",
    "arneses",
    "enganches",
    "identidad",
    "instalar_auditoria",
    "lectores",
    "redaccion",
    "tipo_del_error",
]

__version__ = "0.1.3"


def instalar_auditoria(
    servidor: Any,
    *,
    nombre: str,
    config: Any = None,
    transporte: str = "stdio",
    version: str | None = None,
    commit: str | None = None,
    enganche: str | None = None,
) -> Auditor:
    """Engancha la auditoria en el unico punto por donde pasa todo `tools/call`.

    Nunca decorando herramienta por herramienta: asi la N+1 nace auditada, y
    nadie tiene que acordarse.

    Args:
        servidor: el servidor MCP ya construido, con sus herramientas
            registradas. En `mcp` 1.x eso importa: el enganche envuelve el
            handler que hay en la tabla de ruteo en ese momento.
        nombre: como se llama este MCP. Obligatorio; da el archivo, el
            directorio y la variable de entorno `<NOMBRE>_AUDITORIA`.
        config: ruta del `auditoria.toml` del anfitrion. Sin el, la redaccion
            queda cerrada -forma y ningun valor-, que es el estado seguro.
        transporte: `stdio` (una sesion por proceso) o `http` (N por proceso).
            Cambia quien firma el archivo, no quien firma la linea.
        version, commit: del anfitrion, para la cabecera. Sirven para distinguir
            dos procesos que corren codigo distinto y se reportan iguales.
        enganche: forzar uno (`fastmcp4`, `mcp1x`) en vez de detectarlo.

    Returns:
        El `Auditor`, para que el `check` del MCP publique su `estado()`.
    """
    auditor = Auditor(
        nombre,
        config=config,
        transporte=transporte,
        framework=enganche,
        version=version,
        commit=commit,
    )
    cual = enganche or enganches.detectar(servidor)
    auditor.framework = cual
    if cual == "fastmcp4":
        from lucky_auditoria.enganches import fastmcp4

        fastmcp4.instalar(servidor, auditor)
    elif cual == "mcp1x":
        from lucky_auditoria.enganches import mcp1x

        mcp1x.instalar(servidor, auditor)
    else:
        raise ValueError(f"lucky-auditoria: enganche desconocido {cual!r}")
    return auditor

"""Un anfitrion de mentira, para que el paquete se pruebe como se usa.

El paquete no puede probarse contra su propia configuracion -no tiene: las
listas son del anfitrion-, asi que aca se arma uno minimo. Es la misma forma que
va a usar cada MCP real, y por eso el kit de `lucky_auditoria.pruebas` corre en
esta suite tambien: si el kit se rompe, se rompe aca antes que en un retrofit.
"""

from pathlib import Path

import pytest

CONFIG = """
[argumentos]
action = { tipo = "str", largo_max = 32 }
name = { tipo = "str", largo_max = 128 }
lineas = { tipo = "int" }

[herramientas]
opacas = ["ssh"]

[huellas]
campos = ["token"]

[retorno]
failed = "fallaron"
total_operations = "total"

[conteos.summary]
total_items = "total"
failed = "fallaron"
succeeded = "salieron"
"""


@pytest.fixture
def config(tmp_path) -> Path:
    ruta = tmp_path / "auditoria.toml"
    ruta.write_text(CONFIG, encoding="utf-8")
    return ruta

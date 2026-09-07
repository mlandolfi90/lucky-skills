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


@pytest.fixture(autouse=True, scope="session")
def _la_suite_no_ensucia_la_maquina():
    """Ninguna prueba puede dejar un registro en el estado del usuario REAL.

    No es higiene: es el defecto que este paquete persigue, cometido por su
    propia suite. Paso de verdad -tests del modo crudo escribiendo archivos con
    el centinela adentro en el `%LOCALAPPDATA%` de quien corria pytest-, y lo
    encontro mirar el disco, no leer los tests.

    La trampa que lo causo tiene nombre: apuntar la variable a un archivo en
    `tmp_path` NO alcanza, porque desde R1 el modo crudo ignora la ruta elegida
    y va al estado del usuario a proposito. Cada fixture tiene que mover
    `LOCALAPPDATA` y `XDG_STATE_HOME` tambien.
    """
    import os

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
    real = Path(base) if base else Path.home() / ".local" / "state"
    sospechoso = real / "registro_auditoria"
    antes = sospechoso.exists()
    yield
    if not antes and sospechoso.exists():
        dejados = [str(p) for p in sospechoso.rglob("*") if p.is_file()]
        raise AssertionError(
            f"la suite escribio en el estado del usuario real: {sospechoso}\n"
            + "\n".join(dejados[:10])
        )

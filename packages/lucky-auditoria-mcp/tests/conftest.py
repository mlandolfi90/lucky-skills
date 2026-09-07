"""Un anfitrion de mentira, para que el paquete se pruebe como se usa.

El paquete no puede probarse contra su propia configuracion -no tiene: las
listas son del anfitrion-, asi que aca se arma uno minimo. Es la misma forma que
va a usar cada MCP real, y por eso el kit de `lucky_auditoria.pruebas` corre en
esta suite tambien: si el kit se rompe, se rompe aca antes que en un retrofit.
"""

from pathlib import Path

import pytest

from lucky_auditoria.pruebas import guardas_del_entorno

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


# Las tres guardas del entorno salen del KIT, no de una copia local. Es el
# mismo motivo por el que el kit existe: un modismo que hay que copiar a mano
# se copia mal. La tercera nacio preguntando si la carpeta existia antes, o sea
# que se apagaba sola en la maquina donde uno ya se habia ensuciado, y asi
# dejo pasar un defecto entero hasta el CI. Si el anfitrion la hereda, esa
# version rota no puede reaparecer en un repo.
#
# El paquete es su propio anfitrion: vigila SU repo, que es `parents[1]`.
globals().update(guardas_del_entorno(Path(__file__).resolve().parents[1]))

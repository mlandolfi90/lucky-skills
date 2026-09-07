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
    """Ninguna prueba puede dejar un registro fuera de su `tmp_path`.

    No es higiene: es el defecto que este paquete persigue, cometido por su
    propia suite. Paso de verdad -tests del modo crudo escribiendo archivos con
    el centinela adentro en el `%LOCALAPPDATA%` de quien corria pytest-, y lo
    encontro mirar el disco, no leer los tests.

    Desde R1 de auditar-mcp 1.5.0 el peligro se MUDO, y por eso esta guarda
    mira dos lugares en vez de uno:

    - el estado del usuario, que ya no se usa nunca. Si aparece algo ahi, es
      que quedo codigo de la version anterior.
    - **el repo de este mismo paquete**, que es el peligro nuevo: ahora todo
      va a `<proyecto>/registro_auditoria/`, y un test que se olvide de apuntar
      el proyecto a su `tmp_path` -o de mover el cwd, bajo HTTP- lo escribe
      aca adentro. Es el mismo incidente que motivo R1, cometido por la suite
      que lo prueba.
    """
    import os

    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
    estado = Path(base) if base else Path.home() / ".local" / "state"
    repo = Path(__file__).resolve().parents[1]
    sospechosos = [estado / "registro_auditoria", repo / "registro_auditoria"]
    antes = {s: s.exists() for s in sospechosos}
    yield
    for sospechoso in sospechosos:
        if not antes[sospechoso] and sospechoso.exists():
            dejados = [str(p) for p in sospechoso.rglob("*") if p.is_file()]
            raise AssertionError(
                f"la suite escribio fuera de su tmp_path: {sospechoso}\n"
                + "\n".join(dejados[:10])
            )

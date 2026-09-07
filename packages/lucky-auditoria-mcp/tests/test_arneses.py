"""El catalogo de arneses, que es la lista blanca del entorno.

El mismo entorno que trae la identidad trae los tokens del arnes, asi que la
declaracion tiene que ser la lista: `campos` nombra una por una las variables
que se leen, y ningun otro codigo del paquete toca `os.environ` para armar una
linea.
"""

import ast
from pathlib import Path

from lucky_auditoria import arneses
from lucky_auditoria.arneses import Arnes, detectar, prohibidas

SRC = Path(arneses.__file__).parent


class TestNingunaVariableDeclaradaEsUnSecreto:
    def test_el_catalogo_vigente_esta_limpio(self):
        assert prohibidas() == {}

    def test_la_guarda_cazaria_uno_nuevo(self):
        # El control positivo. Una guarda que solo prueba ausencia se cumple
        # sola cuando el codigo no llego ahi: hay que ver que dice que no.
        malo = Arnes(id="x", testigo="X_SESSION", campos={"X_API_TOKEN": "token"})

        assert prohibidas((malo,)) == {"x": ["X_API_TOKEN"]}

    def test_tambien_mira_el_testigo(self):
        malo = Arnes(id="y", testigo="Y_SECRET_KEY")

        assert prohibidas((malo,))["y"] == ["Y_SECRET_KEY"]


class TestSoloLaDeclaracionLeeElEntorno:
    def test_nadie_mas_toca_os_environ_para_armar_una_linea(self):
        """Una guarda de AST, no un `grep`.

        La propiedad es que la lectura del entorno este concentrada. Si se
        dispersa, la lista blanca deja de ser la lista: cada `os.environ.get`
        suelto es una variable que nadie declaro y que igual puede terminar en
        el archivo.

        Dos exentos, cada uno con su motivo:

        - `registro.py` lee el INTERRUPTOR (`<MCP>_AUDITORIA`), que es
          configuracion del operador y no viaja a ninguna linea. Hasta 0.3.3
          leia tambien `LOCALAPPDATA` y `XDG_STATE_HOME`; desde R1 de 1.5.0 no
          hay estado del usuario y esas dos ya no se tocan. Esta frase decia lo
          contrario hasta que alguien la leyo al lado del codigo.
        - `pruebas/__init__.py` mira el estado del usuario para comprobar que la
          suite NO escribio ahi. Es la guarda que vigila el lugar prohibido, o
          sea lo contrario de armar una linea con el.
        """
        exentos = {"arneses.py", "registro.py", "pruebas/__init__.py"}
        culpables = {}
        for ruta in SRC.rglob("*.py"):
            relativa = ruta.relative_to(SRC).as_posix()
            if relativa in exentos or "__pycache__" in ruta.parts:
                continue
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if (
                    isinstance(nodo, ast.Attribute)
                    and nodo.attr == "environ"
                    and isinstance(nodo.value, ast.Name)
                    and nodo.value.id == "os"
                ):
                    culpables.setdefault(relativa, []).append(nodo.lineno)

        assert culpables == {}


class TestDetectar:
    def test_reconoce_a_claude_code_por_su_testigo(self):
        entorno = {
            "CLAUDE_CODE_SESSION_ID": "abc",
            "CLAUDE_PROJECT_DIR": "C:/repos/mi-repo",
        }

        assert detectar(entorno) == {
            "id": "claude-code",
            "sesion": "abc",
            "proyecto": "C:/repos/mi-repo",
        }

    def test_sin_testigo_no_inventa_nada(self):
        assert detectar({})["id"] == "desconocido"

    def test_un_campo_ausente_queda_en_none_y_no_en_cadena_vacia(self):
        # `None` y `""` se leen distinto: uno dice "no vino", el otro dice
        # "vino vacio", y confundirlos hace que un registro afirme de mas.
        assert detectar({"CLAUDE_CODE_SESSION_ID": "abc"})["proyecto"] is None

    def test_no_se_lee_ninguna_variable_fuera_de_la_declaracion(self):
        entorno = {
            "CLAUDE_CODE_SESSION_ID": "abc",
            "CLAUDE_CODE_OAUTH_TOKEN": "no-deberia-salir-de-aca",
        }

        assert "no-deberia-salir-de-aca" not in str(detectar(entorno))

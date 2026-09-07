"""La herramienta que lee el registro, y los tres limites que la vuelven segura.

Exponer el registro por una herramienta lo pone al alcance de cualquier cliente
conectado. Los tres limites no son adornos: sin el primero se filtran
credenciales, sin el segundo el archivo crece con copias de si mismo, y sin el
tercero el lector comete la familia de defectos que vino a cazar.

Todo en proceso, sin transporte: lo que se puede probar sin HTTP se prueba sin
HTTP. Lo que falta -que el gancho dispare de verdad sobre un servidor HTTP
vivo- lo mide mtk-chr, que es quien tiene uno.
"""

import json

import pytest
from conftest import CONFIG

from lucky_auditoria import Auditor
from lucky_auditoria.herramienta import NOMBRE, TOPE_MAXIMO, Lector


@pytest.fixture
def auditor(tmp_path, monkeypatch):
    # Bajo HTTP el registro va a `./registro_auditoria/` del servicio (R1), o
    # sea al CWD. Sin mover el cwd, esta suite lo escribiria en el repo del
    # paquete: la guarda de sesion de `conftest.py` lo caza, pero es mejor no
    # llegar ahi.
    servicio = tmp_path / "servicio"
    servicio.mkdir()
    monkeypatch.chdir(servicio)
    config = tmp_path / "auditoria.toml"
    config.write_text(CONFIG, encoding="utf-8")
    a = Auditor("mcp-de-prueba", config=config, transporte="http", version="0.2.0")
    monkeypatch.setenv(a.variable, "1")
    return a


@pytest.fixture
def lector(auditor):
    return Lector(auditor)


class TestLimite1SoloElRedactado:
    def test_no_lista_los_archivos_crudos(self, auditor, lector, monkeypatch):
        auditor.registrar("project", {"action": "list"})
        redactado = auditor.ruta()
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar("ssh", {"clave": "una-password"}, respuesta="{}")
        crudo = auditor.ruta()
        assert crudo.exists() and crudo != redactado

        nombres = [a.name for a in lector.archivos()]

        assert redactado.name in nombres
        # Ni por nombre: decir "hay tres que no te muestro" ya cuenta cuantas
        # sesiones de depuracion hubo.
        assert crudo.name not in nombres
        assert not any("CRUDA" in n for n in nombres)

    def test_una_linea_cruda_en_un_archivo_redactado_se_descarta_y_se_dice(
        self, auditor, lector
    ):
        # Defensa en profundidad, y honesta: descartarla en silencio dejaria a
        # la herramienta afirmando que devolvio todo.
        auditor.registrar("project", {"action": "list"})
        with auditor.ruta().open("a", encoding="utf-8") as f:
            f.write(json.dumps({"modo": "crudo", "respuesta": "un-secreto"}) + "\n")

        salida = lector.leer()

        assert salida["omitidas_por_crudas"] == 1
        assert "un-secreto" not in json.dumps(salida)

    def test_ningun_valor_crudo_sale_por_ninguna_accion(self, auditor, lector, monkeypatch):
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar("ssh", {"clave": "pa55w0rd-centinela"}, respuesta="{}")
        monkeypatch.setenv(auditor.variable, "1")
        auditor.registrar("project", {"action": "list"})

        todo = json.dumps(
            {a: json.loads(lector(a)) for a in ("estado", "listar", "leer", "rechazos")},
            default=str,
        )

        assert "pa55w0rd-centinela" not in todo

    def test_cazar_dice_por_que_viene_vacio(self, lector):
        # `[]` a secas se leeria como "no hay nada que cazar", que es una
        # afirmacion que esta herramienta no puede hacer.
        salida = lector.cazar()

        assert salida["candidatos"] == []
        assert "CRUDO" in salida["aviso"]


class TestLimite2SuRetornoEsOpaco:
    def test_la_llamada_se_anota_pero_el_retorno_no(self, auditor):
        # Quien leyo el registro es informacion forense de primera; QUE leyo
        # seria el registro adentro del registro.
        auditor.registrar(
            NOMBRE,
            {"action": "leer"},
            retorno={"fallaron": 3},
            respuesta='{"lineas": [{"sesion": "abc"}]}',
        )

        linea = json.loads(auditor.ruta().read_text(encoding="utf-8").splitlines()[-1])

        assert linea["herramienta"] == NOMBRE
        assert linea["argumentos"] == {"action": "leer"}
        assert "retorno" not in linea
        assert "respuesta" not in linea

    def test_leer_dos_veces_no_hace_crecer_el_archivo_con_copias(self, auditor, lector):
        auditor.registrar("project", {"action": "list"})
        for _ in range(3):
            salida = lector.leer()
            auditor.registrar(NOMBRE, {"action": "leer"}, respuesta=json.dumps(salida))

        texto = auditor.ruta().read_text(encoding="utf-8")

        # Sin la opacidad, la tercera lectura traeria las dos anteriores
        # anidadas y el archivo crece solo.
        assert "lineas" not in texto

    def test_lo_decide_el_paquete_y_no_el_config_del_anfitrion(self, tmp_path, monkeypatch):
        # Un anfitrion que se olvida de declararlo se llevaria la recursion
        # puesta: no es un dato suyo, es una propiedad de esta herramienta.
        estado = tmp_path / "estado"
        estado.mkdir()
        monkeypatch.setenv("LOCALAPPDATA", str(estado))
        monkeypatch.setenv("XDG_STATE_HOME", str(estado))
        sin_config = Auditor("otro-mcp", config=None, transporte="http")
        monkeypatch.setenv(sin_config.variable, "1")
        sin_config.registrar(NOMBRE, {}, retorno={"total": 9}, respuesta="{}")

        linea = json.loads(sin_config.ruta().read_text(encoding="utf-8").splitlines()[-1])

        assert "retorno" not in linea


class TestLimite3PaginaYDiceQueQuedoAfuera:
    def test_dice_cuantas_quedaron_afuera(self, auditor, lector):
        for i in range(10):
            auditor.registrar("project", {"action": "list", "name": f"p{i}"})

        salida = lector.leer(limite=3)

        assert salida["devueltas"] == 3
        assert salida["total"] == 10
        assert salida["quedaron_afuera"] == 7
        assert salida["siguiente_salteo"] == 3

    def test_la_ultima_pagina_no_promete_otra(self, auditor, lector):
        for i in range(4):
            auditor.registrar("project", {"action": "list", "name": f"p{i}"})

        salida = lector.leer(limite=3, salteo=3)

        assert salida["devueltas"] == 1
        assert salida["quedaron_afuera"] == 0
        assert salida["siguiente_salteo"] is None

    def test_un_limite_absurdo_se_recorta_al_tope(self, auditor, lector):
        """Con MAS lineas que el tope, que es lo unico que prueba algo.

        La primera version escribia UNA linea y pedia un millon: devolvia una,
        `1 <= TOPE_MAXIMO` daba verde, y el test pasaba igual con el tope
        borrado. Lo caza la reversion, no la lectura -desde adentro se ve una
        asercion razonable.
        """
        auditor.registrar("project", {"action": "list"})
        with auditor.ruta().open("a", encoding="utf-8") as f:
            for i in range(TOPE_MAXIMO + 5):
                f.write(json.dumps({"cuando": f"2026-01-01T00:00:{i:04d}Z"}) + "\n")

        salida = lector.leer(limite=10**9)

        assert salida["total"] > TOPE_MAXIMO
        assert salida["devueltas"] == TOPE_MAXIMO
        assert salida["quedaron_afuera"] > 0

    def test_un_limite_de_cero_no_devuelve_el_archivo_entero(self, auditor, lector):
        for i in range(5):
            auditor.registrar("project", {"action": "list", "name": f"p{i}"})

        # `0` no puede caer en un "sin limite": es el valor que manda un
        # cliente que no entendio el parametro.
        assert lector.leer(limite=0)["devueltas"] == 1


class TestLosFiltros:
    def test_filtra_por_herramienta_y_por_rango(self, auditor, lector):
        auditor.registrar("project", {"action": "list"})
        auditor.registrar("node", {"action": "list"})

        assert lector.leer(herramienta="node")["total"] == 1
        assert lector.leer(desde="2999-01-01T00:00:00+00:00")["total"] == 0
        assert lector.leer(hasta="2999-01-01T00:00:00+00:00")["total"] == 2

    def test_filtra_por_sesion(self, auditor, lector):
        auditor.registrar("project", {"action": "list"})
        sesion = json.loads(auditor.ruta().read_text(encoding="utf-8").splitlines()[-1])["sesion"]

        assert lector.leer(sesion=sesion)["total"] == 1
        assert lector.leer(sesion="otra-sesion")["total"] == 0

    def test_la_cabecera_no_se_devuelve_como_si_fuera_una_llamada(self, auditor, lector):
        auditor.registrar("project", {"action": "list"})

        assert lector.leer()["total"] == 1


class TestElDespacho:
    def test_una_accion_desconocida_devuelve_un_error_con_codigo(self, lector):
        salida = json.loads(lector("borrar_todo"))

        assert salida["error_code"] == "ACCION_DESCONOCIDA"
        assert "leer" in salida["acciones"]

    def test_todas_las_acciones_declaradas_responden(self, auditor, lector):
        from lucky_auditoria.herramienta import ACCIONES

        auditor.registrar("project", {"action": "list"})
        for accion in ACCIONES:
            json.loads(lector(accion))

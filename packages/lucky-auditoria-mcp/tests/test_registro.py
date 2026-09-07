"""El registro: la cabecera, la respuesta en crudo y el fondo de un error.

Tres de estas guardas las encontro la pasada de REVERSION, no el diseño: romper
"el modo crudo escribe la respuesta" no ponia en rojo ningun test, y esa es
exactamente la mitad de la linea sobre la que vive `cazar`. Una decision sin un
test que la cace no esta protegida, este donde este escrita.
"""

import json

import pytest
from conftest import CONFIG

from lucky_auditoria import Auditor
from lucky_auditoria.registro import MAX_RESPUESTA, tipo_del_error


@pytest.fixture
def auditor(tmp_path, monkeypatch):
    config = tmp_path / "auditoria.toml"
    config.write_text(CONFIG, encoding="utf-8")
    a = Auditor("mcp-de-prueba", config=config, version="1.2.3", commit="abc123")
    monkeypatch.setenv(a.variable, str(tmp_path / "reg.jsonl"))
    return a


def _lineas(auditor):
    return [json.loads(x) for x in auditor.ruta().read_text(encoding="utf-8").splitlines()]


class TestLaRespuestaEnModoCrudo:
    def test_el_crudo_escribe_la_respuesta_entera(self, auditor, monkeypatch):
        # Sin esto, `cazar` no tiene contra que comparar el argumento y el
        # paquete pierde su lector principal.
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar("x", {"name": "R1"}, respuesta='{"nodos": ["R1"]}')

        assert _lineas(auditor)[-1]["respuesta"] == '{"nodos": ["R1"]}'

    def test_el_redactado_NO_escribe_la_respuesta(self, auditor):
        # El control opuesto: en redactado la respuesta es material sin filtrar.
        auditor.registrar("x", {}, respuesta="lo que sea")

        assert "respuesta" not in _lineas(auditor)[-1]

    def test_una_respuesta_larga_se_corta_y_dice_de_cuanto(self, auditor, monkeypatch):
        monkeypatch.setenv(auditor.variable, "crudo")
        larga = "a" * (MAX_RESPUESTA + 500)
        auditor.registrar("x", {}, respuesta=larga)

        linea = _lineas(auditor)[-1]
        assert len(linea["respuesta"]) == MAX_RESPUESTA
        # Recortar sin decirlo es la familia de defectos que este registro vino
        # a cazar: no puede cometerla el registro mismo.
        assert linea["respuesta_recortada_de"] == len(larga)


class TestLaCabecera:
    def test_se_escribe_con_la_primera_linea_y_una_sola_vez(self, auditor):
        # No al arrancar: un servidor que nadie uso no deja rastro.
        assert not auditor.ruta().exists()
        auditor.registrar("x", {})
        auditor.registrar("y", {})

        lineas = _lineas(auditor)
        assert lineas[0]["tipo"] == "cabecera"
        assert [x.get("tipo") for x in lineas[1:]] == [None, None]

    def test_declara_el_alcance_del_archivo(self, auditor):
        auditor.registrar("x", {})
        cabecera = _lineas(auditor)[0]

        assert cabecera["mcp"] == {
            "nombre": "mcp-de-prueba",
            "version": "1.2.3",
            "commit": "abc123",
        }
        assert cabecera["transporte"] == "stdio"
        assert cabecera["esquema"] >= 1
        # Sin la huella de la config, un argumento recortado no se distingue de
        # uno completo al leer el registro tres semanas despues.
        assert cabecera["redaccion"]["huella"].startswith("sha256:")
        assert cabecera["redaccion"]["valida"] is True

    def test_no_lleva_valores_de_configuracion_ni_del_entorno(self, auditor, monkeypatch):
        monkeypatch.setenv("UN_TOKEN_DEL_ARNES", "no-deberia-aparecer")
        auditor.registrar("x", {})

        assert "no-deberia-aparecer" not in auditor.ruta().read_text(encoding="utf-8")


class TestElFondoDeUnError:
    def test_se_devuelve_el_tipo_real_y_el_envoltorio_que_lo_tapaba(self):
        class ErrorDeDominio(Exception):
            pass

        class ToolError(Exception):
            pass

        try:
            try:
                raise ErrorDeDominio("nodo inexistente")
            except ErrorDeDominio as causa:
                raise ToolError("envuelto") from causa
        except ToolError as e:
            real, envoltorio = tipo_del_error(e)

        assert (real, envoltorio) == ("ErrorDeDominio", "ToolError")

    def test_sin_envoltorio_no_se_inventa_uno(self):
        assert tipo_del_error(ValueError("x")) == ("ValueError", None)

    def test_una_cadena_circular_no_cuelga(self):
        a, b = ValueError("a"), TypeError("b")
        a.__cause__ = b
        b.__cause__ = a

        # Sin el tope, esto no vuelve nunca: el registro seria el que tumba lo
        # que audita.
        real, _ = tipo_del_error(a)
        assert real in {"ValueError", "TypeError"}


class TestElNombreEsObligatorio:
    def test_sin_nombre_no_se_puede_construir(self):
        # Al mover el enganche de subclase a middleware, la declaracion del
        # nombre se cayo y NADA fallo: el registro escribio
        # `mcp-sin-nombre-auditoria-...`, forma correcta y origen equivocado.
        with pytest.raises(ValueError, match="obligatorio"):
            Auditor("")

    def test_la_variable_sale_del_nombre(self, auditor):
        assert auditor.variable == "MCP_DE_PRUEBA_AUDITORIA"


class TestElCheckAvisaSiLaRedaccionQuedoCerrada:
    def test_una_config_rota_se_ve_en_el_estado(self, tmp_path, monkeypatch):
        # Encontrado probando la cadena entera a mano: con la config sin cargar,
        # `rechazos` devolvia [] sobre un registro que SI tenia fallos adentro.
        # No rompe nada, escribe igual, y por eso no se nota.
        a = Auditor("mcp-de-prueba", config=tmp_path / "no-existe.toml")
        monkeypatch.setenv(a.variable, str(tmp_path / "reg.jsonl"))

        estado = a.estado()
        assert estado["redaccion"] == "cerrada"
        assert "no se pudo leer" in estado["redaccion_motivo"]

    def test_con_la_config_sana_lo_dice_igual(self, auditor):
        # El campo va SIEMPRE. Uno que aparece solo cuando algo anda mal
        # obliga a saber que puede aparecer: el que lee el `check` sano no se
        # entera de que existe, y entonces tampoco lo busca.
        assert auditor.estado()["redaccion"] == "abierta"
        assert "redaccion_motivo" not in auditor.estado()


class TestLaCabeceraDiceSiLaRedaccionREGIA:
    def test_una_redaccion_cerrada_lo_declara_en_la_cabecera(self, tmp_path, monkeypatch):
        # `valida` no se deduce de `huella`: una redaccion cerrada tiene la
        # huella en null, y "no hay huella" se lee igual que "no la calcule".
        # Sin el booleano, un archivo escrito con las listas caidas parece uno
        # escrito con listas que no declaraban nada.
        a = Auditor("mcp-de-prueba", config=tmp_path / "no-existe.toml")
        monkeypatch.setenv(a.variable, str(tmp_path / "reg.jsonl"))
        a.registrar("x", {})

        redaccion = _lineas(a)[0]["redaccion"]
        assert redaccion["valida"] is False
        assert redaccion["huella"] is None
        assert "no se pudo leer" in redaccion["problema"]

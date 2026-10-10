"""El registro: la cabecera, la respuesta en crudo y el fondo de un error.

Tres de estas guardas las encontro la pasada de REVERSION, no el diseño: romper
"el modo crudo escribe la respuesta" no ponia en rojo ningun test, y esa es
exactamente la mitad de la linea sobre la que vive `cazar`. Una decision sin un
test que la cace no esta protegida, este donde este escrita.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from conftest import CONFIG

from lucky_auditoria import Auditor, identidad
from lucky_auditoria.registro import MAX_RESPUESTA, tipo_del_error

CENTINELA = "centinela-del-registro-7c1e"


@pytest.fixture
def auditor(tmp_path, monkeypatch):
    return _construir(tmp_path, monkeypatch)


def _construir(tmp_path, monkeypatch, **extra):
    config = tmp_path / "auditoria.toml"
    config.write_text(CONFIG, encoding="utf-8")
    # El PROYECTO va a `tmp_path`, y no alcanza con apuntar la variable a un
    # archivo: desde R1, el modo crudo ignora la ruta elegida y escribe en la
    # carpeta del proyecto. Sin esto, cada test del modo crudo deja un archivo
    # con el centinela adentro en el repo de quien corre la suite -antes era en
    # su `%LOCALAPPDATA%`; el peligro se mudo, no desaparecio-. Paso, y lo
    # encontro barrer los tests de a uno mirando el disco, no leerlos.
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir(exist_ok=True)
    monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: str(proyecto))
    a = Auditor("mcp-de-prueba", config=config, version="1.2.3", commit="abc123", **extra)
    # Una CARPETA: desde 0.10.0 la ruta absoluta es siempre carpeta (S-11).
    monkeypatch.setenv(a.variable, str(tmp_path / "registro"))
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


class TestElPaqueteDiceUnaSolaVersion:
    """Dos numeros de version en el mismo paquete, y ninguno fallaba.

    Paso: un commit mio dejo `pyproject.toml` en 0.3.2 y `__version__` en
    0.3.3. La causa fue un `sed` que no matcheo -el merge habia traido otro
    numero del que yo esperaba- y no dijo nada: el reemplazo silencioso es un
    no-op, y un no-op se ve igual que un exito.

    Lo encontro otra sesion leyendo el archivo, no la suite. Esta guarda es
    para que la proxima lo encuentre la suite: la version que declara el
    manifiesto y la que expone el paquete son la MISMA cosa dicha dos veces, y
    cuando se separan el que instala y el que importa leen distinto.
    """

    def test_el_manifiesto_y_el_modulo_coinciden(self):
        import tomli

        import lucky_auditoria

        raiz = Path(__file__).resolve().parents[1]
        manifiesto = tomli.loads((raiz / "pyproject.toml").read_text(encoding="utf-8"))

        assert manifiesto["project"]["version"] == lucky_auditoria.__version__


# --- 0.10.0 -----------------------------------------------------------------


class TestLasPalabrasDelInterruptorNoDistinguenMayusculas:
    """S-22: hasta 0.9.0 `CRUDO` no era una palabra: se tomaba como ruta
    RELATIVA y la auditoria se apagaba, con el operador pidiendo encender."""

    @pytest.mark.parametrize(
        ("palabra", "modo"),
        [
            ("CRUDO", "crudo"),
            ("Debug", "crudo"),
            ("TRUE", "redactado"),
            ("Si", "redactado"),
            ("FALSE", "apagado"),
            ("No", "apagado"),
        ],
    )
    def test_cualquier_caja(self, auditor, monkeypatch, palabra, modo):
        monkeypatch.setenv(auditor.variable, palabra)

        assert auditor.modo() == modo


class TestRegistrarNoLevantaPorNada:
    """S-19: "nunca levanta" cubria la escritura y no el cuerpo entero."""

    def test_un_fallo_al_armar_la_ruta_tampoco_levanta(self, auditor, monkeypatch, caplog):
        def revienta():
            raise ValueError(CENTINELA)

        monkeypatch.setattr(auditor, "ruta", revienta)
        with caplog.at_level("WARNING"):
            # Si esto levanta, auditar tumbo la llamada que auditaba.
            auditor.registrar("x", {})

        assert "ValueError" in caplog.text
        assert CENTINELA not in caplog.text, "el mensaje de la excepcion se copio al log"

    def test_el_check_tampoco(self, auditor, monkeypatch):
        def revienta():
            raise ValueError(CENTINELA)

        monkeypatch.setattr(auditor, "ruta", revienta)
        estado = auditor.estado()

        assert estado["archivo"] is None
        assert "ValueError" in estado["motivo"]
        assert CENTINELA not in str(estado)

    def test_un_id_de_sesion_que_no_sirve_de_nombre_no_sale_de_la_carpeta(
        self, auditor, monkeypatch, tmp_path
    ):
        # El id viene del entorno. Con un separador, `Path.with_name` levantaba.
        monkeypatch.setattr(identidad, "id_de_sesion", lambda: "../../afuera")
        auditor.registrar("x", {})

        ruta = auditor.ruta()
        assert ruta.exists() and ruta.parent == tmp_path / "registro"
        assert "afuera" not in ruta.name
        # La linea sigue llevando el id tal cual: el nombre es lo que se protege.
        assert _lineas(auditor)[-1]["sesion"] == "../../afuera"


class TestElArchivoLoFirmaElTransporte:
    """U: bajo stdio firma la sesion (R2), bajo HTTP el pid. Hasta 0.9.0
    `if _SESION_DEL_TRANSPORTE:` preguntaba por el objeto `ContextVar`, que
    siempre es verdadero, y bajo stdio todo archivo salia firmado con el pid."""

    def test_stdio_firma_con_la_sesion(self, auditor, monkeypatch):
        monkeypatch.setattr(identidad, "id_de_sesion", lambda: "sesion-de-stdio")
        assert auditor.transporte == "stdio"

        nombre = auditor.ruta().name
        assert "sesion-de-stdio" in nombre
        assert f"pid{os.getpid()}" not in nombre

    def test_http_firma_con_el_pid(self, auditor, monkeypatch):
        monkeypatch.setattr(identidad, "id_de_sesion", lambda: "sesion-de-http")
        auditor.transporte = "http"

        nombre = auditor.ruta().name
        assert f"pid{os.getpid()}" in nombre
        assert "sesion-de-http" not in nombre


class TestUnaCabeceraQueFalloSeReintenta:
    def test_la_llamada_siguiente_la_escribe(self, auditor, monkeypatch):
        """S-21: hasta 0.9.0 se marcaba escrita ANTES de escribirla. Si
        escribirla fallaba, el archivo quedaba entero sin cabecera: sin MCP,
        sin esquema y sin la huella de la redaccion."""
        original = auditor._cabecera
        intentos = []

        def falla_la_primera(modo):
            intentos.append(modo)
            if len(intentos) == 1:
                raise OSError("disco lleno")
            return original(modo)

        monkeypatch.setattr(auditor, "_cabecera", falla_la_primera)
        auditor.registrar("x", {})
        auditor.registrar("y", {})

        lineas = _lineas(auditor)
        assert lineas[0]["tipo"] == "cabecera"
        assert [x.get("herramienta") for x in lineas[1:]] == ["y"]


class TestElCheckDaDosFechas:
    def test_mas_viejo_es_la_primera_linea_y_no_la_ultima_escritura(self, auditor):
        """X, de lucky-tool-mtk-chr: hasta 0.9.0 `mas_viejo` era el menor
        mtime, y en un archivo que solo crece el mtime es la ULTIMA escritura:
        con un solo archivo, "lo mas viejo" era lo recien escrito."""
        auditor.registrar("x", {})
        propio = auditor.ruta()
        firma = identidad.escritor(auditor.transporte)

        def hermano(nombre, primera, mtime):
            otro = propio.with_name(propio.name.replace(firma, nombre))
            otro.write_text(json.dumps({"tipo": "cabecera", "cuando": primera}) + "\n", "utf-8")
            os.utime(otro, (mtime, mtime))

        # El de contenido mas viejo, tocado hace un minuto. `Z` como lo escribe
        # un hermano TypeScript.
        hermano("viejo", "2026-01-01T00:00:00Z", time.time() - 60)
        # Y el mas quieto, con contenido mas nuevo.
        marzo = datetime(2026, 3, 1, tzinfo=timezone.utc)
        hermano("quieto", "2026-09-01T00:00:00+00:00", marzo.timestamp())

        acumulado = auditor.estado()["acumulado"]

        assert acumulado["archivos"] == 3
        assert acumulado["mas_viejo"] == "2026-01-01T00:00:00+00:00"
        assert acumulado["escritura_mas_vieja"] == marzo.isoformat()


class TestElCheckAvisaSinRetornoNiConteos:
    """R, de lucky-tool-mtk-chr: sin `[retorno]` ni `[conteos]` un rechazo
    adentro de una respuesta exitosa se anota ok. Aviso, no falla: un MCP sin
    herramientas por lote no los necesita."""

    def test_sin_las_dos_secciones_avisa(self, tmp_path, monkeypatch):
        config = tmp_path / "solo-argumentos.toml"
        config.write_text('[argumentos]\naction = { tipo = "str" }\n', encoding="utf-8")
        a = Auditor("mcp-sin-lotes", config=config)
        # Apagado incluso: la configuracion se juzga igual.
        monkeypatch.setenv(a.variable, "0")

        assert "sin [retorno] ni [conteos]" in a.estado()["redaccion_aviso"]

    def test_con_retorno_no_avisa(self, auditor):
        assert "redaccion_aviso" not in auditor.estado()


class TestElDestinoVaEnLaCabecera:
    """Z1, de lucky-tool-mtk-chr (plano de construccion, F06 y R-081): ni el
    evento ni la cabecera decian a que sistema iban las llamadas. Un proceso que
    habla con un solo destino lo declara una vez, y va en la cabecera."""

    def test_el_destino_declarado(self, tmp_path, monkeypatch):
        a = _construir(tmp_path, monkeypatch, destino="routeros://chr-lab:22")
        a.registrar("x", {})

        assert _lineas(a)[0]["destino"] == "routeros://chr-lab:22"

    def test_sin_destino_la_cabecera_lo_dice_con_null(self, auditor):
        auditor.registrar("x", {})

        cabecera = _lineas(auditor)[0]
        assert "destino" in cabecera and cabecera["destino"] is None

    @pytest.mark.parametrize(
        ("declarado", "queda"),
        [
            (f"ssh://admin:{CENTINELA}@10.0.0.1:22/r?token={CENTINELA}", "ssh://10.0.0.1:22/r"),
            (f"admin:{CENTINELA}@10.0.0.1", "10.0.0.1"),
            (f"https://api.local/v1#{CENTINELA}", "https://api.local/v1"),
        ],
    )
    def test_un_destino_con_credenciales_se_anota_como_lugar(
        self, tmp_path, monkeypatch, declarado, queda
    ):
        a = _construir(tmp_path, monkeypatch, destino=declarado)
        a.registrar("x", {})

        assert _lineas(a)[0]["destino"] == queda
        assert CENTINELA not in a.ruta().read_text(encoding="utf-8")

    def test_un_destino_que_no_es_texto_no_se_construye(self):
        with pytest.raises(TypeError):
            Auditor("mcp-de-prueba", destino=42)


class TestElIdDelPedidoVaEnLaLinea:
    """Z2, de lucky-tool-mtk-chr (plano de construccion, paso 6, y R-039): la
    auditoria escribe al cierre; la llegada y el pedido cortado a mitad los
    anota el log del borde, L1 y L2, con un id por pedido. Con ese id en la
    linea, los dos se cruzan."""

    def test_el_id_que_anoto_el_borde(self, auditor):
        marca = identidad.anotar_id_del_pedido("a1b2c3")
        try:
            auditor.registrar("x", {})
        finally:
            identidad.olvidar_id_del_pedido(marca)
        auditor.registrar("y", {})

        lineas = _lineas(auditor)
        assert lineas[1]["id_pedido"] == "a1b2c3"
        assert "id_pedido" not in lineas[2], "el id de un pedido quedo pegado al siguiente"

    def test_un_id_sin_forma_de_id_no_se_anota_y_se_avisa(self, auditor, monkeypatch, caplog):
        monkeypatch.setattr(identidad, "_aviso_id_raro_dado", False)
        with caplog.at_level("WARNING"):
            marca = identidad.anotar_id_del_pedido("x" * 500)
            try:
                auditor.registrar("x", {})
            finally:
                identidad.olvidar_id_del_pedido(marca)

        assert "id_pedido" not in _lineas(auditor)[-1]
        assert "id de pedido" in caplog.text

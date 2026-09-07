"""La redaccion: por forma, no por nombre, y cerrada ante cualquier duda."""

import pytest
from conftest import CONFIG

from lucky_auditoria.redaccion import Redaccion, cargar


@pytest.fixture
def reglas(tmp_path):
    ruta = tmp_path / "auditoria.toml"
    ruta.write_text(CONFIG, encoding="utf-8")
    return cargar(ruta)


class TestUnCampoEsSeguroPorNombreMasTipoMasLargo:
    def test_el_tipo_declarado_pasa_entero(self, reglas):
        assert reglas.argumentos_de("x", {"action": "list"}) == {"action": "list"}

    def test_el_tipo_equivocado_cae_a_forma(self, reglas):
        # El caso que motiva la regla: `lineas` esta declarado `int`, y el
        # cliente manda un str. Si la lista mirara solo el nombre, ese valor
        # llegaria al disco -y el registro anota ANTES de que nadie valide.
        limpio = reglas.argumentos_de("x", {"lineas": "un-secreto"})

        assert limpio == {"lineas": {"tipo": "str", "largo": 10}}

    def test_un_bool_no_cuela_por_un_int(self, reglas):
        # En Python `bool` es subclase de `int`, asi que sin la comparacion
        # aparte esto pasaria por un entero declarado.
        assert reglas.argumentos_de("x", {"lineas": True}) == {"lineas": {"tipo": "bool"}}

    def test_pasarse_del_largo_cae_a_forma(self, reglas):
        largo = "a" * 200
        assert reglas.argumentos_de("x", {"action": largo}) == {
            "action": {"tipo": "str", "largo": 200}
        }

    def test_un_nombre_no_declarado_cae_a_forma_y_no_al_vacio(self, reglas):
        # A diferencia del retorno: omitirlo dejaria al registro mintiendo
        # sobre lo que se PIDIO.
        assert reglas.argumentos_de("x", {"que_es_esto": "valor"}) == {
            "que_es_esto": {"tipo": "str", "largo": 5}
        }


class TestOpacasYHuellas:
    def test_una_opaca_no_deja_ni_los_nombres(self, reglas):
        limpio = reglas.argumentos_de("ssh", {"comando": "enable secret hola", "host": "r1"})

        assert limpio == {"_opaco": True, "operaciones": None}

    def test_una_opaca_cuenta_las_operaciones_y_nada_mas(self, reglas):
        limpio = reglas.argumentos_de("ssh", {"operations": [{"a": 1}, {"b": 2}]})

        assert limpio == {"_opaco": True, "operaciones": 2}

    def test_una_huella_correlaciona_sin_guardar(self, reglas):
        uno = reglas.argumentos_de("x", {"token": "abc123"})
        otro = reglas.argumentos_de("y", {"token": "abc123"})

        assert uno["token"].startswith("sha256:")
        assert "abc123" not in uno["token"]
        # El punto de la huella: el mismo valor en dos superficies se cruza.
        assert uno["token"] == otro["token"]


class TestElRetornoTieneElDefectoAlReves:
    def test_una_clave_no_declarada_no_se_anota_ni_en_forma(self, reglas):
        assert reglas.retorno_de({"nodos": ["R1", "R2", "R3"]}) is None

    def test_una_lista_declarada_se_anota_como_conteo(self, reglas):
        assert reglas.retorno_de({"failed": [1, 2]}) == {"fallaron": 2}

    def test_los_conteos_anidados_salen_del_bloque(self, reglas):
        resumen = reglas.retorno_de({"summary": {"total_items": 15, "failed": 3, "succeeded": 12}})

        assert resumen == {"total": 15, "fallaron": 3, "salieron": 12}

    def test_nunca_salen_nombres_solo_cuentas(self, reglas):
        resumen = reglas.retorno_de({"failed": ["R1", "R2"], "total_operations": 5})

        assert resumen == {"fallaron": 2, "total": 5}
        assert "R1" not in str(resumen)

    def test_un_retorno_que_no_es_de_lote_no_deja_rastro(self, reglas):
        assert reglas.retorno_de({"status": "ok"}) is None
        assert reglas.retorno_de("texto suelto") is None
        assert reglas.retorno_de(None) is None


class TestFallaCerradoSinRomperElArranque:
    def test_sin_ruta_queda_cerrada(self):
        reglas = cargar(None)

        assert reglas.problema is not None
        assert reglas.argumentos_de("x", {"action": "list"}) == {
            "action": {"tipo": "str", "largo": 4}
        }

    def test_un_toml_roto_queda_cerrado_y_no_levanta(self, tmp_path):
        ruta = tmp_path / "roto.toml"
        ruta.write_text("[argumentos\nesto = no cierra", encoding="utf-8")

        assert "no es un TOML valido" in cargar(ruta).problema

    def test_una_seccion_desconocida_cierra_la_puerta(self, tmp_path):
        # El modo de fallo con nombre: una regla que el operador cree escrita y
        # no rige. El archivo PARECE configurado.
        ruta = tmp_path / "raro.toml"
        ruta.write_text('[redaccion]\npor_defecto = "completo"\n', encoding="utf-8")
        reglas = cargar(ruta)

        assert "secciones desconocidas" in reglas.problema
        assert reglas.argumentos == {}

    def test_un_argumento_sin_tipo_valido_cierra_la_puerta(self, tmp_path):
        ruta = tmp_path / "sin-tipo.toml"
        ruta.write_text('[argumentos]\nname = { largo_max = 10 }\n', encoding="utf-8")

        assert "no declara un tipo valido" in cargar(ruta).problema

    def test_el_archivo_ausente_no_levanta(self, tmp_path):
        assert cargar(tmp_path / "no-existe.toml").problema is not None


class TestLaHuellaDeLaConfigViajaALaCabecera:
    def test_dos_configuraciones_distintas_dan_huellas_distintas(self, tmp_path):
        una = tmp_path / "a.toml"
        otra = tmp_path / "b.toml"
        una.write_text(CONFIG, encoding="utf-8")
        otra.write_text(
            CONFIG + '\n[argumentos]\nextra = { tipo = "str" }\n', encoding="utf-8"
        )

        assert cargar(una).huella_config != cargar(otra).huella_config

    def test_una_redaccion_cerrada_no_tiene_huella(self):
        assert Redaccion.cerrada("por la prueba").huella_config is None


class TestElRespaldoDeTomlEnPython310:
    """`tomllib` entro en 3.11; abajo el paquete usa `tomli`, y eso hay que medirlo.

    Esta maquina solo tiene 3.12, asi que el import gateado por version
    (`except ModuleNotFoundError: import tomli`) NO se ejercita aca: lo corre el
    CI en su celda de 3.10, y ese CI todavia no se ejecuto nunca.

    Lo que SI se puede medir sin un 3.10 es la otra mitad de la afirmacion: que
    la version pineada de `tomli` parsea esta configuracion igual que `tomllib`.
    Si difirieran, un MCP en 3.10 tendria otras listas blancas que el mismo MCP
    en 3.13 -mismo archivo, otra redaccion- y nadie lo notaria.

    Se declara lo que cubre y lo que no, en vez de dejar la version pineada
    afirmando mas de lo medido.
    """

    def test_tomli_parsea_esta_config_igual_que_tomllib(self):
        import tomli
        import tomllib

        crudo = CONFIG.encode("utf-8")

        assert tomli.loads(crudo.decode("utf-8")) == tomllib.loads(crudo.decode("utf-8"))

    def test_una_redaccion_cargada_con_tomli_da_las_mismas_reglas(self, tmp_path, monkeypatch):
        import tomli

        from lucky_auditoria import redaccion as modulo

        ruta = tmp_path / "auditoria.toml"
        ruta.write_text(CONFIG, encoding="utf-8")
        con_tomllib = cargar(ruta)
        monkeypatch.setattr(modulo, "tomllib", tomli)
        con_tomli = cargar(ruta)

        assert con_tomli.argumentos == con_tomllib.argumentos
        assert con_tomli.opacas == con_tomllib.opacas
        assert con_tomli.conteos == con_tomllib.conteos
        # La huella sale de los BYTES del archivo, no del parseo: tiene que ser
        # la misma, o dos procesos del mismo MCP declararian configuraciones
        # distintas en sus cabeceras.
        assert con_tomli.huella_config == con_tomllib.huella_config

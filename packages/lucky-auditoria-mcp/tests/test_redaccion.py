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


# Lo que esta configuracion TIENE que dar, escrito a mano y no derivado de
# ningun parser. Es lo unico que se puede comprobar en 3.10, donde no hay
# `tomllib` contra que comparar.
_ESPERADO = {
    "argumentos": {
        "action": {"tipo": "str", "largo_max": 32},
        "name": {"tipo": "str", "largo_max": 128},
        "lineas": {"tipo": "int"},
    },
    "herramientas": {"opacas": ["ssh"]},
    "huellas": {"campos": ["token"]},
    "retorno": {"failed": "fallaron", "total_operations": "total"},
    "conteos": {
        "summary": {"total_items": "total", "failed": "fallaron", "succeeded": "salieron"}
    },
}


class TestElRespaldoDeTomlEnPython310:
    """`tomllib` entro en 3.11; abajo el paquete usa `tomli`, y eso hay que medirlo.

    Si los dos parsearan distinto, un MCP en 3.10 tendria otras listas blancas
    que el mismo MCP en 3.13 -mismo archivo, otra redaccion- y nadie lo notaria.

    La primera version de esta clase importaba `tomllib` a secas y ROMPIA el CI
    en 3.10, que es justo la version que venia a cubrir: en 3.10 `tomllib` no
    existe. El test escrito para medir el piso no podia correr en el piso.

    Se arregla comparando contra una expectativa ESCRITA A MANO, que vale en
    las dos, y dejando la comparacion cruzada solo donde hay con que cruzar. Un
    `skip` a secas habria dejado 3.10 sin medir nada, que es lo que se queria
    evitar.
    """

    def test_tomli_parsea_esta_config_como_se_espera(self):
        import tomli

        assert tomli.loads(CONFIG) == _ESPERADO

    def test_y_tomllib_da_lo_mismo_donde_existe(self):
        # Solo >=3.11. En 3.10 no hay nada que cruzar, y el test de arriba ya
        # midio lo que importa.
        tomllib = pytest.importorskip(
            "tomllib", reason="tomllib entro en 3.11; en 3.10 rige el test de arriba"
        )

        assert tomllib.loads(CONFIG) == _ESPERADO

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


class TestContenedores:
    """Listas y diccionarios: declarables, y cerrados por omision.

    Antes no se podian declarar: un `tipo = "list"` no degradaba ese campo,
    cerraba la redaccion entera. El anfitrion no tenia forma de decir "este de
    aca lo quiero", y hay MCP cuya unica pregunta interesante vive adentro de
    un contenedor -en uno de escritura, `operations` ES la intencion-.
    """

    def _reglas(self, tmp_path, cuerpo):
        ruta = tmp_path / "auditoria.toml"
        ruta.write_text(cuerpo, encoding="utf-8")
        return cargar(ruta)

    def test_declarar_el_tipo_no_abre_el_contenido(self, tmp_path):
        """El defecto, y es el que sostiene la promesa del paquete.

        Una lista blanca por NOMBRE no puede responder por lo anidado: el
        nombre `operations` no dice nada de lo que el llamador metio en
        `operations[0]["datos"]`. Por eso abrirlo es una decision escrita y no
        algo que se hereda por declarar el tipo.
        """
        reglas = self._reglas(tmp_path, '[argumentos]\noperations = { tipo = "list" }\n')

        limpio = reglas.argumentos_de("x", {"operations": [{"secreto": "CENTINELA"}]})

        assert limpio == {"operations": {"tipo": "list", "largo": 1}}
        assert "CENTINELA" not in str(limpio)

    def test_con_contenido_completo_el_anfitrion_lo_abre(self, tmp_path):
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\noperations = { tipo = "list", contenido = "completo" }\n',
        )
        pedido = [{"accion": "create", "tipo": "dcim.site"}]

        assert reglas.argumentos_de("x", {"operations": pedido}) == {"operations": pedido}

    def test_un_dict_tambien(self, tmp_path):
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\nfilters = { tipo = "dict", contenido = "completo" }\n',
        )

        assert reglas.argumentos_de("x", {"filters": {"site": "lab"}}) == {
            "filters": {"site": "lab"}
        }

    def test_el_tipo_equivocado_sigue_cayendo_a_forma(self, tmp_path):
        """Declarar `list` no vuelve seguro a un str que se llame igual."""
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\noperations = { tipo = "list", contenido = "completo" }\n',
        )

        limpio = reglas.argumentos_de("x", {"operations": "no-soy-una-lista"})

        assert limpio == {"operations": {"tipo": "str", "largo": 16}}

    def test_un_contenedor_enorme_cae_a_forma(self, tmp_path):
        """Lo que `largo_max` hace con una cadena, y por el mismo motivo.

        Un tope existe para que una linea del registro no se coma el archivo.
        """
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\noperations = { tipo = "list", contenido = "completo", '
            "elementos_max = 3 }\n",
        )

        assert reglas.argumentos_de("x", {"operations": [1, 2, 3]}) == {"operations": [1, 2, 3]}
        assert reglas.argumentos_de("x", {"operations": [1, 2, 3, 4]}) == {
            "operations": {"tipo": "list", "largo": 4}
        }

    def test_un_contenido_desconocido_cierra_la_puerta(self, tmp_path):
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\noperations = { tipo = "list", contenido = "casi" }\n',
        )

        assert "contenido='casi'" in reglas.problema

    def test_contenido_completo_sobre_un_escalar_cierra_la_puerta(self, tmp_path):
        """Un ajuste que no hace nada es peor que ninguno.

        En un `str` no hay contenido que abrir, asi que aceptarlo en silencio
        dejaria al operador creyendo que declaro algo.
        """
        reglas = self._reglas(
            tmp_path,
            '[argumentos]\naction = { tipo = "str", contenido = "completo" }\n',
        )

        assert "no tiene contenido que abrir" in reglas.problema

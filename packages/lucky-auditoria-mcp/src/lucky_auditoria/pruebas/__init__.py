"""Kit de pruebas que el anfitrion HEREDA, para no reescribir las guardas.

Un retrofit termina cuando estas pruebas pasan en el repo anfitrion, no cuando
el codigo compila. La mayoria son de FUGA y no de formato: buscan un secreto
centinela en el TEXTO CRUDO del archivo, no en el objeto parseado, porque un
`json.loads` esconde justo lo que se quiere ver.

## Como se usa

    # tests/test_auditoria.py del anfitrion
    from lucky_auditoria import Auditor
    from lucky_auditoria.pruebas import KitDeAuditoria

    class TestAuditoria(KitDeAuditoria):
        def construir(self, tmp_path):
            return Auditor("mi-mcp", config="config/auditoria.toml")

pytest colecta los metodos heredados, asi que el que agrega un arnes o una
herramienta opaca hereda la guarda sin escribirla.

## Las dos expectativas, y por que la segunda

Las guardas son conscientes del MODO, con expectativa invertida: en redactado
el centinela NO aparece; en crudo SI debe aparecer. Sin la segunda, una
redaccion rota que borra todo pasa en verde y el modo de depurar deja de
depurar sin que nadie lo note. Una guarda que solo prueba ausencia se cumple
sola cuando el codigo no llego ahi.
"""

import json
import os
from pathlib import Path

import pytest

from lucky_auditoria import arneses

# Un valor que no puede aparecer por casualidad en ningun lado.
CENTINELA = "pa55w0rd-centinela-8f21c3"


class KitDeAuditoria:
    """Las guardas que todo MCP auditado tiene que pasar.

    El anfitrion implementa `construir` y hereda el resto.
    """

    # -- lo unico que el anfitrion escribe ----------------------------------

    def construir(self, tmp_path: Path):
        """Devolver el `Auditor` del anfitrion, ya configurado."""
        raise NotImplementedError(
            "El anfitrion tiene que implementar `construir(tmp_path)` "
            "devolviendo su Auditor."
        )

    # La herramienta y el argumento con los que se ejercita. El anfitrion los
    # pisa si sus nombres son otros; los de aca no tienen por que existir.
    herramienta_normal = "prueba"
    argumento_no_declarado = "parametro_que_no_existe"

    # -- infraestructura ----------------------------------------------------

    @pytest.fixture
    def auditor(self, tmp_path, monkeypatch):
        """Un auditor apuntado a `tmp_path`, con el interruptor en redactado.

        El `chdir` no es cosmetico: un interruptor mal escrito no deja de
        escribir, escribe con el directorio VACIO -o sea, en el cwd- y una
        prueba que solo mira `tmp_path` pasa con el interruptor roto. Al correr
        desde un directorio limpio, ese archivo aparece donde se lo ve.
        """
        cwd = tmp_path / "cwd-limpio"
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        auditor = self.construir(tmp_path)
        monkeypatch.setenv(auditor.variable, str(tmp_path / "registro.jsonl"))
        return auditor

    def _texto(self, auditor) -> str:
        """El archivo tal cual esta en disco. Nunca parseado."""
        ruta = auditor.ruta()
        assert ruta is not None, "el auditor deberia estar encendido en esta prueba"
        return ruta.read_text(encoding="utf-8")

    # -- fuga, en los dos modos --------------------------------------------

    def test_redactado_no_escribe_el_valor_de_un_argumento_no_declarado(self, auditor):
        auditor.registrar(
            self.herramienta_normal, {self.argumento_no_declarado: CENTINELA}
        )

        assert CENTINELA not in self._texto(auditor)

    def test_crudo_SI_escribe_el_valor(self, auditor, monkeypatch):
        # La expectativa invertida. Sin esta, una redaccion que borra todo pasa
        # en verde y el modo de depurar deja de depurar en silencio.
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(
            self.herramienta_normal, {self.argumento_no_declarado: CENTINELA}
        )

        assert CENTINELA in self._texto(auditor)

    def test_el_archivo_crudo_se_llama_a_gritos_y_cada_linea_lo_dice(
        self, auditor, monkeypatch
    ):
        monkeypatch.setenv(auditor.variable, "crudo")
        auditor.registrar(self.herramienta_normal, {})

        assert "CRUDA-" in auditor.ruta().name
        assert '"modo": "crudo"' in self._texto(auditor)

    def test_una_herramienta_opaca_no_deja_ni_los_nombres_ni_el_tamano(self, auditor):
        if not auditor.redaccion.opacas:
            pytest.skip("este MCP no declara herramientas opacas")
        opaca = sorted(auditor.redaccion.opacas)[0]
        auditor.registrar(opaca, {"comando": CENTINELA, "usuario": "admin"})

        texto = self._texto(auditor)
        assert CENTINELA not in texto
        assert "comando" not in texto
        # El largo tambien filtra: mide la password. La primera version de esta
        # guarda buscaba `str(len(CENTINELA))` en el texto y daba rojo porque
        # ese numero aparecia en la marca de tiempo: era una carrera entre dos
        # cosas distintas, no una prueba. Se pregunta por la PROPIEDAD -que lo
        # anotado sea solo la forma opaca- en vez de por un numero suelto.
        anotado = json.loads(texto.splitlines()[-1])["argumentos"]
        assert set(anotado) == {"_opaco", "operaciones"}
        assert "largo" not in texto

    def test_el_mensaje_de_una_excepcion_no_se_copia(self, auditor):
        # El texto de una excepcion arrastra lo que se le paso a la herramienta.
        # Por eso se anota el TIPO, no el mensaje.
        auditor.registrar(
            self.herramienta_normal,
            {},
            resultado="error",
            error=type(ValueError(CENTINELA)).__name__,
        )

        assert CENTINELA not in self._texto(auditor)

    # -- el interruptor -----------------------------------------------------

    def test_apagado_no_escribe_nada_en_ningun_lado(self, auditor, monkeypatch, tmp_path):
        monkeypatch.delenv(auditor.variable, raising=False)
        auditor.registrar(self.herramienta_normal, {self.argumento_no_declarado: CENTINELA})

        assert auditor.ruta() is None
        # Ni archivo vacio ni directorio creado, y tampoco en el cwd: el
        # `chdir` de la fixture es lo que hace visible este segundo caso.
        assert list(Path(os.getcwd()).iterdir()) == []
        assert not list(tmp_path.glob("**/*.jsonl"))

    def test_una_palabra_desconocida_apaga_y_lo_dice(self, auditor, monkeypatch, caplog):
        # Caso medido: la variable quedo en `crude`, no estaba en la lista, se
        # tomo como RUTA, y la auditoria quedo redactada escribiendo
        # `crude-<sesion>.jsonl` sin que nadie se enterara.
        #
        # La primera correccion agrego el aviso y siguio escribiendo, que es la
        # mitad peor: un aviso que no cambia lo que pasa no es una proteccion.
        monkeypatch.setenv(auditor.variable, "cruod")
        with caplog.at_level("WARNING"):
            modo = auditor.modo()

        assert modo == "apagado"
        assert auditor.ruta() is None
        assert any("APAGADA" in r.message for r in caplog.records)

    def test_una_ruta_RELATIVA_apaga_en_vez_de_escribir_en_el_cwd(
        self, auditor, monkeypatch, tmp_path
    ):
        # Una ruta relativa cuelga el archivo del directorio de trabajo, que un
        # MCP hereda de quien lo lanzo: es el mismo daño que el directorio por
        # defecto vino a evitar, pedido por el operador sin querer.
        monkeypatch.setenv(auditor.variable, "registro/auditoria.jsonl")
        auditor.registrar(self.herramienta_normal, {})

        assert auditor.ruta() is None
        assert list(Path(os.getcwd()).iterdir()) == []

    def test_si_no_se_puede_crear_el_directorio_no_se_escribe_en_ningun_lado(
        self, auditor, monkeypatch
    ):
        # Habia una caida al cwd -"mejor el cwd que perder el registro"- y
        # estaba mal: no escribir no rompe nada, y la caida pone el archivo con
        # credenciales justo en el repo ajeno.
        monkeypatch.setenv(auditor.variable, "1")

        def no_se_puede(*_a, **_k):
            raise OSError("permiso denegado")

        monkeypatch.setattr(Path, "mkdir", no_se_puede)
        auditor.registrar(self.herramienta_normal, {})

        assert auditor.directorio_por_defecto() is None
        assert auditor.ruta() is None
        assert list(Path(os.getcwd()).iterdir()) == []

    # -- el nombre del archivo ---------------------------------------------

    def test_las_marcas_van_aunque_la_ruta_sea_explicita(self, auditor, monkeypatch, tmp_path):
        destino = tmp_path / "elegido.jsonl"
        monkeypatch.setenv(auditor.variable, str(destino))

        nombre = auditor.ruta().name
        assert nombre.startswith(auditor.nombre), "falta el nombre del MCP"
        assert "elegido" in nombre, "se perdio la eleccion del operador"

    def test_el_default_no_es_el_cwd(self, auditor, monkeypatch):
        # El cwd de un MCP por stdio lo hereda de quien lo lanzo, y eso deja
        # archivos con credenciales en repos ajenos.
        monkeypatch.setenv(auditor.variable, "1")

        assert Path(os.getcwd()) not in auditor.ruta().parents

    # -- no romper ----------------------------------------------------------

    def test_un_fallo_de_escritura_no_levanta(self, auditor, monkeypatch):
        def no_se_puede(*_a, **_k):
            raise OSError("disco lleno")

        monkeypatch.setattr(Path, "open", no_se_puede)
        # Si esto levanta, auditar se volvio un modo de fallo nuevo.
        auditor.registrar(self.herramienta_normal, {})

    def test_contar_mal_no_tumba_el_estado(self, auditor, monkeypatch):
        def no_se_puede(*_a, **_k):
            raise OSError("permiso denegado")

        monkeypatch.setattr(Path, "glob", no_se_puede)
        estado = auditor.estado()

        assert estado["acumulado"]["error"] == "OSError"
        assert estado["modo"] == "redactado"

    # -- el catalogo de arneses --------------------------------------------

    def test_ningun_arnes_declara_una_variable_que_se_llama_como_un_secreto(self):
        # Por CLASE, no caso por caso: corre sobre todo arnes registrado,
        # incluido el que el anfitrion agregue desde su propio paquete.
        assert arneses.prohibidas() == {}

    # -- la configuracion ---------------------------------------------------

    def test_la_redaccion_del_anfitrion_se_cargo_de_verdad(self, auditor):
        # Una redaccion cerrada por error de sintaxis pasa TODAS las pruebas de
        # fuga de arriba, porque no escribe nada. Esta es la que lo distingue de
        # una redaccion que funciona.
        assert auditor.redaccion.problema is None, auditor.redaccion.problema
        assert auditor.redaccion.argumentos, "el anfitrion no declaro ningun argumento seguro"
        assert auditor.redaccion.huella_config


def verificar_enganche(servidor) -> None:
    """Que el gancho este en la TABLA DE RUTEO, no solo declarado.

    Un gancho declarado no es un gancho que corre -medido: `on_initialize` de
    fastmcp 4.0.2 nunca dispara. Y un test que llama al override directo pasa
    por definicion: hay que preguntarle al servidor que va a ejecutar de verdad,
    para que falle el dia que el SDK deje de ligarlo.
    """
    from lucky_auditoria import enganches

    cual = enganches.detectar(servidor)
    if cual == "fastmcp4":
        from lucky_auditoria.enganches.fastmcp4 import AuditoriaMiddleware

        instalados = list(getattr(servidor, "middleware", []) or [])
        assert any(isinstance(m, AuditoriaMiddleware) for m in instalados), (
            "el middleware de auditoria no esta en la lista del servidor: "
            f"hay {[type(m).__name__ for m in instalados]}"
        )
        return
    from mcp.types import CallToolRequest

    handler = servidor.request_handlers.get(CallToolRequest)
    assert getattr(handler, "_lucky_auditoria", False), (
        "el handler de `tools/call` que el servidor tiene registrado no es el auditado"
    )

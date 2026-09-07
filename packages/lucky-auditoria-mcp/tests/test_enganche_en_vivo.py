"""El enganche, ejercitado por un `tools/call` de verdad sobre toda la pila.

La guarda estructural -`verificar_enganche`- pregunta que tiene registrado el
servidor, y eso NO prueba que el framework lo llame. Aca entra un cliente en
proceso contra la INSTANCIA (`fastmcp.Client(mcp)`, no una URL): pasa por ruteo,
validacion y la cadena de middlewares igual que un cliente remoto, y cuesta
milisegundos. La forma es de lucky-tool-mtk-chr, que la midio primero.

Las dos guardas conviven y ninguna sobra: la estructural no prueba que el
framework lo llame, y la del cliente no prueba que el gancho este en la lista si
alguien la reemplaza.

## Lo que estas pruebas MIDEN, y no suponen

Dos cosas que no se pueden contestar leyendo el codigo propio:

1. **En que punto de la cadena escribe el registro.** Si escribiera DESPUES de
   que el framework valida, la fuga que motiva la lista blanca por tipo no
   existiria -y el test que la prueba pasaria igual, sin cubrir nada. La
   pregunta la hizo mtk-chr y era la correcta.
2. **Que le llega al gancho cuando la herramienta DEVUELVE un rechazo.** El
   `is_error` del framework marca sus excepciones, no los rechazos del MCP.
"""

import json

import pytest
from conftest import CONFIG
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from lucky_auditoria import instalar_auditoria
from lucky_auditoria.pruebas import verificar_enganche

CENTINELA = "Sup3rS3cr3t0-centinela"


@pytest.fixture
def servidor(tmp_path, monkeypatch):
    """Un MCP de dos verbos, con la auditoria enganchada como en un repo real."""
    estado = tmp_path / "estado"
    estado.mkdir()
    monkeypatch.setenv("LOCALAPPDATA", str(estado))
    monkeypatch.setenv("XDG_STATE_HOME", str(estado))
    config = tmp_path / "auditoria.toml"
    config.write_text(CONFIG, encoding="utf-8")

    mcp = FastMCP("mcp-de-prueba", mask_error_details=False)

    @mcp.tool
    def leer(name: str, lineas: int = 10) -> str:
        """`lineas` declarado int: el esquema publicado dice int."""
        return json.dumps({"name": name, "lineas": lineas})

    @mcp.tool
    def rechazar(name: str) -> str:
        """Devuelve el rechazo en el retorno, sin levantar. El camino 2."""
        return json.dumps({"ok": False, "error_code": "NOMBRE_TOMADO"})

    @mcp.tool
    def explotar(name: str) -> str:
        """Levanta. El camino 1, que fastmcp envuelve en ToolError."""
        raise ValueError(f"el dominio dijo que no: {CENTINELA}")

    auditor = instalar_auditoria(
        mcp, nombre="mcp-de-prueba", config=config, version="0.2.0"
    )
    monkeypatch.setenv(auditor.variable, "1")
    return mcp, auditor


def _lineas(auditor):
    texto = auditor.ruta().read_text(encoding="utf-8")
    return [json.loads(x) for x in texto.splitlines() if '"tipo": "cabecera"' not in x]


class TestElGanchoDisparaDeVerdad:
    async def test_una_llamada_real_deja_su_linea(self, servidor):
        mcp, auditor = servidor
        async with Client(mcp) as c:
            await c.call_tool("leer", {"name": "R1", "lineas": 5})

        linea = _lineas(auditor)[-1]
        assert linea["herramienta"] == "leer"
        assert linea["argumentos"]["name"] == "R1"
        assert linea["resultado"] == "ok"
        assert linea["duracion_ms"] >= 0

    def test_y_ademas_esta_en_la_lista_del_servidor(self, servidor):
        # La guarda estructural. No sobra: la de arriba no la cubre si alguien
        # reemplaza la lista por otra cosa que tambien funcione.
        mcp, _ = servidor
        verificar_enganche(mcp)


class TestDondeEscribeEnLaCadena:
    async def test_el_registro_anota_ANTES_de_que_el_framework_valide(self, servidor):
        """La medicion que pidio mtk-chr, y la unica que contesta la pregunta.

        El esquema publicado dice `lineas: int`; el cliente manda un str. Si el
        registro anotara DESPUES de la validacion, esta llamada nunca llegaria
        al gancho y la fuga que motiva la lista blanca por TIPO no existiria.

        Medido con fastmcp 4.0.3: la linea SE ESCRIBE, con el valor rechazado
        adentro. O sea que la lista blanca por tipo es necesaria de verdad, y
        no una precaucion teorica.
        """
        mcp, auditor = servidor
        async with Client(mcp) as c:
            with pytest.raises(ToolError):
                await c.call_tool("leer", {"name": "R1", "lineas": CENTINELA})

        lineas = _lineas(auditor)
        assert lineas, "el gancho no vio la llamada invalida: el registro anota post-validacion"
        # Lo llego a ver, y la lista blanca por tipo lo tacho: el valor no esta.
        assert CENTINELA not in auditor.ruta().read_text(encoding="utf-8")
        assert lineas[-1]["argumentos"]["lineas"] == {"tipo": "str", "largo": len(CENTINELA)}
        assert lineas[-1]["error"] == "ValidationError"

    async def test_el_framework_SI_escribe_el_valor_rechazado_en_su_propio_log(
        self, servidor, caplog
    ):
        """Una superficie que el registro no cubre, y que hay que nombrar.

        Encontrado midiendo lo de arriba, sin buscarlo: fastmcp 4.0.3 loguea
        `Invalid arguments for tool 'leer'` con el `input` COMPLETO adentro
        -`'input': 'Sup3rS3cr3t0'`-. O sea que el valor que la lista blanca
        tacho del registro sale igual por el log del proceso.

        El paquete no puede arreglarlo: es el log del framework, no el nuestro.
        Lo que si puede es no dejar que pase inadvertido, y por eso hay un test
        que lo afirma: si algun dia fastmcp deja de hacerlo, este test se pone
        rojo y el aviso del README sobra. Mientras tanto, el log del proceso de
        un MCP con auditoria es material sensible aunque el registro no lo sea.
        """
        mcp, _ = servidor
        with caplog.at_level("WARNING"):
            async with Client(mcp) as c:
                with pytest.raises(ToolError):
                    await c.call_tool("leer", {"name": "R1", "lineas": CENTINELA})

        # Control del INSTRUMENTO antes que del hecho. `fastmcp` tiene
        # `propagate=False` y dos RichHandler propios (medido en 4.0.3), asi
        # que un capturador enganchado en la raiz podria no ver nada -y
        # entonces la prueba no diria que no hay fuga, diria que no la estamos
        # mirando. Con pytest 9.1.1 SI llega, medido: un record de
        # `fastmcp.server.server`. Si algun dia deja de llegar, esto lo dice.
        assert caplog.records, (
            "el capturador no vio NINGUN record: `fastmcp` no propaga a la raiz "
            "y el instrumento dejo de servir. Este test no puede afirmar nada "
            "hasta arreglarlo."
        )

        salida = " ".join(r.getMessage() for r in caplog.records)
        # La asercion es POSITIVA a proposito, y eso la hace inmune al fallo de
        # arriba: si el capturador no viera nada, `salida` seria vacia y este
        # assert daria rojo. Una guarda que afirmara la AUSENCIA del centinela
        # se cumpliria sola con el instrumento roto -es la familia de "la guarda
        # que se cumple sola", esta vez del lado del que mide.
        assert CENTINELA in salida, (
            "fastmcp ya no escribe el valor rechazado en su log: sacar el aviso "
            "del README y borrar este test"
        )


class TestLosTresCaminosDeUnError:
    async def test_1_la_herramienta_levanta(self, servidor):
        mcp, auditor = servidor
        async with Client(mcp) as c:
            with pytest.raises(ToolError):
                await c.call_tool("explotar", {"name": "R1"})

        linea = _lineas(auditor)[-1]
        assert linea["resultado"] == "error"
        # El tipo del FONDO, no el envoltorio de fastmcp.
        assert linea["error"] == "ValueError"
        assert linea.get("envoltorio") == "ToolError"
        # Y el mensaje no se copia: arrastra los argumentos.
        assert CENTINELA not in auditor.ruta().read_text(encoding="utf-8")

    async def test_2_la_herramienta_devuelve_el_rechazo(self, servidor):
        """El camino que ningun framework puede ver por su cuenta.

        `is_error` marca las excepciones del framework, no los rechazos del
        MCP. Un gancho que le creyera anotaria `ok` sobre el 100% de los
        rechazos -medido por mtk-chr sobre un servidor donde una red de errores
        garantiza que ningun verbo levante.
        """
        mcp, auditor = servidor
        async with Client(mcp) as c:
            resultado = await c.call_tool("rechazar", {"name": "R1"})

        # Primero lo que dice el framework, para que quede escrito que no basta.
        assert getattr(resultado, "is_error", False) is False
        # Y despues lo que anota el registro, que es lo que pasó de verdad.
        linea = _lineas(auditor)[-1]
        assert linea["resultado"] == "error"
        assert linea["error"] == "NOMBRE_TOMADO"

    async def test_3_el_lote_que_sale_bien_con_fallos_adentro(self, servidor):
        mcp, auditor = servidor

        @mcp.tool
        def por_lote(name: str) -> str:
            return json.dumps({"summary": {"total_items": 15, "failed": 3, "succeeded": 12}})

        async with Client(mcp) as c:
            await c.call_tool("por_lote", {"name": "*"})

        linea = _lineas(auditor)[-1]
        # La llamada salio bien Y tres cosas no pasaron. No se contradicen.
        assert linea["resultado"] == "ok"
        assert linea["retorno"] == {"total": 15, "fallaron": 3, "salieron": 12}


class TestLaHerramientaNaceAuditada:
    async def test_una_tool_agregada_despues_queda_auditada_sin_tocar_nada(self, servidor):
        # El motivo de enganchar en un punto y no decorar verbo por verbo: la
        # N+1 nace auditada, y nadie tiene que acordarse.
        mcp, auditor = servidor

        @mcp.tool
        def nueva(name: str) -> str:
            return "ok"

        async with Client(mcp) as c:
            await c.call_tool("nueva", {"name": "R9"})

        assert _lineas(auditor)[-1]["herramienta"] == "nueva"

    async def test_el_cliente_se_anota_de_su_handshake(self, servidor):
        mcp, auditor = servidor
        async with Client(mcp) as c:
            await c.call_tool("leer", {"name": "R1"})

        # Nombra al producto, no a la sesion -por eso no sirve para atribuir-,
        # pero tiene que llegar: si es None, el gancho lo esta buscando mal.
        assert _lineas(auditor)[-1]["cliente"] is not None

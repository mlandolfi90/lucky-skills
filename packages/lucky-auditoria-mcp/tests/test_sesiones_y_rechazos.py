"""Cuarta tanda de lucky-tool-mtk-chr sobre 0.8.0 (ficha CAP-7824fd652563).

J. Bajo HTTP todas las sesiones salian con el mismo id: la funcion que lo
   cambiaba existia y nadie la llamaba, y era una global del modulo que dos
   llamadas concurrentes se pisaban. Aca: dos clientes, dos ids, y el id de
   cada linea es el de la sesion que la hizo aunque las llamadas se crucen.
K. Un rechazo con otra forma se anotaba ok: solo se reconocia `error_code`.
"""

import asyncio
import contextlib
import json
import socket
from contextlib import asynccontextmanager

import httpx2
import pytest
from conftest import CONFIG
from fastmcp import Client, FastMCP

from lucky_auditoria import identidad, instalar_auditoria
from lucky_auditoria.rechazos import RECHAZO_SIN_CATEGORIA, codigo_de_error


def _servidor(tmp_path, monkeypatch, transporte):
    proyecto = tmp_path / "el-repo-que-llamo"
    proyecto.mkdir(exist_ok=True)
    monkeypatch.setattr(identidad, "raiz_del_proyecto", lambda: str(proyecto))
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "auditoria.toml"
    config.write_text(CONFIG, encoding="utf-8")
    mcp = FastMCP("mcp-de-prueba", mask_error_details=False)

    @mcp.tool
    async def leer(name: str, lineas: int = 10) -> str:
        # Un `await` real: deja que la otra sesion se meta en el medio.
        await asyncio.sleep(0.01)
        return json.dumps({"name": name, "lineas": lineas})

    @mcp.tool
    def candado(name: str) -> str:
        return json.dumps({"ok": False, "bloqueado_por_candado": True})

    @mcp.tool
    def negarse(name: str) -> str:
        return json.dumps({"ok": False})

    auditor = instalar_auditoria(
        mcp, nombre="mcp-de-prueba", config=config, version="0.9.0", transporte=transporte
    )
    monkeypatch.setenv(auditor.variable, "1")
    return mcp, auditor


def _lineas(auditor):
    texto = auditor.ruta().read_text(encoding="utf-8")
    return [json.loads(x) for x in texto.splitlines() if '"tipo": "cabecera"' not in x]


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@asynccontextmanager
async def _servido_por_http(mcp):
    """El servidor de verdad, por streamable-http en un puerto de esta maquina.

    El transporte en memoria (`Client(mcp)`) reconstruye la sesion por pedido,
    igual que stdio: ahi `session_id` cambia en cada llamada y no mide nada.
    El `mcp-session-id` estable por cliente solo existe por HTTP.
    """
    puerto = _puerto_libre()
    tarea = asyncio.create_task(
        mcp.run_async(transport="http", host="127.0.0.1", port=puerto, show_banner=False)
    )
    url = f"http://127.0.0.1:{puerto}/mcp"
    try:
        # Listo cuando contesta un `initialize` crudo (mide 1,3 s). Esperarlo
        # con `fastmcp.Client(url).ping()` tardaba casi 30 s por reintentos.
        async with httpx2.AsyncClient(timeout=2) as h:
            for _ in range(200):
                await asyncio.sleep(0.05)
                if tarea.done():
                    raise RuntimeError("el servidor HTTP de prueba murio antes de contestar")
                with contextlib.suppress(Exception):
                    r = await h.post(url, json={
                        "jsonrpc": "2.0", "id": 0, "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                   "clientInfo": {"name": "listo", "version": "0"}},
                    }, headers=_CABECERAS)
                    if r.status_code == 200:
                        break
        yield url
    finally:
        tarea.cancel()
        with contextlib.suppress(BaseException):
            await tarea


_CABECERAS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


class _ClienteQueDevuelveLaSesion:
    """Un cliente HTTP como los de verdad: toma el `mcp-session-id` que el
    servidor acuña en el `initialize` y lo devuelve en cada pedido.

    Medido con fastmcp 4.0.3: `fastmcp.Client(url)` de este mismo paquete NO lo
    devuelve, asi que con el no se puede medir esto. Claude Code y los
    clientes de mtk si lo devuelven.
    """

    def __init__(self, url):
        self.url = url
        self.sesion = None
        self._n = 0

    async def __aenter__(self):
        self._http = httpx2.AsyncClient(timeout=10)
        r = await self._rpc("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "prueba", "version": "0"},
        })
        self.sesion = r.headers.get("mcp-session-id")
        assert self.sesion, "el servidor no acuño mcp-session-id en el initialize"
        await self._http.post(
            self.url,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers=self._cabeceras(),
        )
        return self

    async def __aexit__(self, *_):
        await self._http.aclose()

    def _cabeceras(self):
        extra = {"mcp-session-id": self.sesion} if self.sesion else {}
        return {**_CABECERAS, **extra}

    async def _rpc(self, metodo, params):
        self._n += 1
        return await self._http.post(
            self.url, json={"jsonrpc": "2.0", "id": self._n, "method": metodo, "params": params},
            headers=self._cabeceras(),
        )

    async def call_tool(self, nombre, argumentos):
        r = await self._rpc("tools/call", {"name": nombre, "arguments": argumentos})
        assert r.status_code == 200, r.text[:200]


class TestBajoHttpCadaSesionTieneSuId:
    async def test_dos_clientes_dos_ids_y_cada_linea_con_el_suyo(self, tmp_path, monkeypatch):
        mcp, auditor = _servidor(tmp_path, monkeypatch, "http")
        sesiones = {}

        async def cliente(url, nombre, veces):
            async with _ClienteQueDevuelveLaSesion(url) as c:
                sesiones[nombre] = c.sesion
                for i in range(veces):
                    await c.call_tool("leer", {"name": f"{nombre}-{i}"})

        # Los dos a la vez: las llamadas se cruzan en el `await` de la herramienta.
        async with _servido_por_http(mcp) as url:
            await asyncio.gather(cliente(url, "A", 3), cliente(url, "B", 3))

        lineas = _lineas(auditor)
        assert len(lineas) == 6
        por_cliente = {}
        for linea in lineas:
            cliente_de = linea["argumentos"]["name"].split("-")[0]
            por_cliente.setdefault(cliente_de, set()).add(linea["sesion"])
        # Cada cliente con UN id, que es el que negocio, y distinto del otro.
        assert por_cliente == {"A": {sesiones["A"]}, "B": {sesiones["B"]}}, por_cliente
        assert sesiones["A"] != sesiones["B"]

    async def test_el_id_no_queda_pegado_al_proceso(self, tmp_path, monkeypatch):
        mcp, auditor = _servidor(tmp_path, monkeypatch, "http")
        async with _servido_por_http(mcp) as url, _ClienteQueDevuelveLaSesion(url) as c:
            await c.call_tool("leer", {"name": "x"})
        # Fuera de la llamada, la identidad vuelve a la del proceso.
        assert identidad.id_de_sesion() != _lineas(auditor)[-1]["sesion"]


class TestBajoStdioLaSesionSigueSiendoElProceso:
    async def test_dos_clientes_un_id(self, tmp_path, monkeypatch):
        # fastmcp 4 bajo stdio da un session_id nuevo por pedido: no sirve, y
        # por eso ahi se ignora. Un proceso, una sesion, un id.
        mcp, auditor = _servidor(tmp_path, monkeypatch, "stdio")
        for nombre in ("A", "B"):
            async with Client(mcp) as c:
                await c.call_tool("leer", {"name": nombre})
        assert len({linea["sesion"] for linea in _lineas(auditor)}) == 1


class TestUnRechazoConOtraFormaSeAnotaComoRechazo:
    @pytest.mark.parametrize(
        ("datos", "codigo"),
        [
            ({"ok": False, "error_code": "NOMBRE_TOMADO"}, "NOMBRE_TOMADO"),
            ({"ok": False, "bloqueado_por_candado": True}, "bloqueado_por_candado"),
            ({"ok": False, "detalle": "x", "sin_permiso": True}, "sin_permiso"),
            ({"ok": False}, RECHAZO_SIN_CATEGORIA),
            ({"ok": False, "reintentable": False}, RECHAZO_SIN_CATEGORIA),
            ({"ok": True, "bloqueado_por_candado": True}, None),
            ({"ok": True}, None),
            ({"status": "ok"}, None),
            ("texto suelto", None),
            (None, None),
        ],
    )
    def test_formas(self, datos, codigo):
        assert codigo_de_error(datos) == codigo

    async def test_por_la_pila_entera(self, tmp_path, monkeypatch):
        mcp, auditor = _servidor(tmp_path, monkeypatch, "http")
        async with Client(mcp) as c:
            await c.call_tool("candado", {"name": "r1"})
            await c.call_tool("negarse", {"name": "r1"})

        con_candado, negado = _lineas(auditor)[-2:]
        assert con_candado["resultado"] == "error"
        assert con_candado["error"] == "bloqueado_por_candado"
        assert negado["resultado"] == "error"
        assert negado["error"] == RECHAZO_SIN_CATEGORIA

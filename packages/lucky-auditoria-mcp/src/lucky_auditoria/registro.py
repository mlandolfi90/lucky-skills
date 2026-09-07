"""El registro: donde escribe, como se llama el archivo, y que lleva cada linea.

Nada de aca puede romper una llamada ni el arranque. Un fallo al auditar que
tumbe la operacion convierte una mejora en un modo de fallo nuevo, asi que todo
lo que puede fallar se avisa por el log del proceso y sigue.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from lucky_auditoria import identidad
from lucky_auditoria.redaccion import Redaccion, cargar

logger = logging.getLogger(__name__)

# Version del esquema de las lineas. Va en la cabecera: un lector que encuentra
# un numero que no conoce puede decirlo en vez de leer mal.
ESQUEMA = 1

_ARCHIVO_POR_DEFECTO = "auditoria.jsonl"
_DIRECTORIO = "registro_auditoria"

# El modo crudo se enciende con una PALABRA, no con un `1`: encenderlo tiene que
# ser un acto deliberado y no el resultado de copiar un ejemplo.
_PALABRAS_CRUDAS = frozenset({"crudo", "crude", "debug", "raw"})
_PALABRAS_APAGADO = frozenset({"", "0", "false", "no"})
_PALABRAS_REDACTADO = frozenset({"1", "true", "si", "yes"})
_PALABRAS = _PALABRAS_CRUDAS | _PALABRAS_APAGADO | _PALABRAS_REDACTADO

# Tope del texto de la respuesta en modo crudo. Una respuesta grande dejaria el
# registro ilegible: se corta y se dice de cuanto.
MAX_RESPUESTA = 20_000

# Tope de la cadena de causas de un error. Una cadena que se muerde la cola
# (`a.__cause__ = b; b.__cause__ = a`) colgaria el servidor, y el registro no
# puede ser el que tumba lo que audita.
MAX_CAUSAS = 10


def tipo_del_error(error: BaseException) -> tuple:
    """El tipo REAL del error y, si difiere, el envoltorio que lo tapaba.

    fastmcp 4 envuelve TODO lo que levanta una herramienta en `ToolError`, asi
    que `type(error).__name__` es siempre lo mismo y el registro llamaria igual
    a los quince fallos distintos. El error de verdad sobrevive en `__cause__`:
    se recorre la cadena hasta el fondo.

    El envoltorio se devuelve aparte y solo cuando difiere, porque distingue dos
    cosas que se leen igual si se anota una sola: `ToolError` sobre
    `NodeNotFound` dice "el dominio lo rechazo"; un `ValidationError` pelado dice
    "falto un argumento".
    """
    fondo = error
    for _ in range(MAX_CAUSAS):
        causa = fondo.__cause__
        if causa is None or causa is fondo:
            break
        fondo = causa
    real = type(fondo).__name__
    envoltorio = type(error).__name__
    return real, (envoltorio if envoltorio != real else None)


def _parece_una_palabra_mal_escrita(valor: str) -> bool:
    """Un valor que quiso ser una palabra clave y no lo es.

    Caso medido: la variable quedo en `crude` -el operador queria el modo
    crudo-, la palabra no estaba en la lista y se tomo como RUTA. La auditoria
    quedo REDACTADA escribiendo un archivo llamado `crude-<sesion>.jsonl`, y
    nadie se entero. El agujero no era la palabra faltante sino el respaldo:
    cualquier palabra suelta se volvia un nombre de archivo plausible, en el
    modo equivocado y en silencio.

    Una ruta de verdad tiene separador o extension. Una palabra pelada casi
    siempre es el typo de una clave, y eso hay que decirlo.
    """
    if valor.lower() in _PALABRAS:
        return False
    return not any(c in valor for c in "/\\.") and " " not in valor


class Auditor:
    """Un MCP que audita. Sin nombre no se puede construir.

    El nombre no es un adorno: da el archivo, la variable de entorno y el
    directorio. Lo que el enganche garantizaba por construccion tiene que viajar
    con el o volverse parametro obligatorio -al mover un enganche de subclase a
    middleware, la declaracion del nombre se cayo y nada fallo: el registro
    escribio `mcp-sin-nombre-auditoria-...`, forma correcta y origen equivocado.
    """

    def __init__(
        self,
        nombre: str,
        *,
        config: Path | str | None = None,
        transporte: str = "stdio",
        framework: str | None = None,
        version: str | None = None,
        commit: str | None = None,
    ) -> None:
        if not nombre or not str(nombre).strip():
            raise ValueError(
                "lucky-auditoria: `nombre` es obligatorio. Sale del manifiesto del "
                "MCP anfitrion (`[project].name`), nunca de una constante copiada."
            )
        self.nombre = str(nombre).strip().lower().replace("_", "-").replace(" ", "-")
        self.transporte = transporte
        self.framework = framework
        self.version = version
        self.commit = commit
        self.redaccion: Redaccion = cargar(config)
        self._candado = threading.Lock()
        self._cabecera_escrita: set = set()
        self._aviso_crudo_dado = False
        self._aviso_palabra_rara_dado = False

    # -- el interruptor -----------------------------------------------------

    @property
    def variable(self) -> str:
        """`<MCP>_AUDITORIA`. Uno solo, y su valor dice el modo o la ruta."""
        return self.nombre.upper().replace("-", "_") + "_AUDITORIA"

    def modo(self) -> str:
        """`apagado`, `redactado` o `crudo`. Apagado por omision, de verdad.

        Apagado de verdad quiere decir sin archivo vacio y sin directorio
        creado: escribir en disco sin que nadie lo haya pedido es una decision
        del operador, no del programa.
        """
        valor = os.environ.get(self.variable, "").strip()
        if valor.lower() in _PALABRAS_CRUDAS:
            return "crudo"
        if valor in _PALABRAS_APAGADO:
            return "apagado"
        if _parece_una_palabra_mal_escrita(valor) and not self._aviso_palabra_rara_dado:
            self._aviso_palabra_rara_dado = True
            logger.warning(
                "%s=%r no es una palabra conocida y no parece una ruta. Se toma "
                "como nombre de archivo y la auditoria queda REDACTADA. Si se "
                "buscaba el modo de depuracion, las palabras son: %s.",
                self.variable,
                valor,
                ", ".join(sorted(_PALABRAS_CRUDAS)),
            )
        return "redactado"

    # -- donde escribe ------------------------------------------------------

    def directorio_por_defecto(self) -> Path:
        """El directorio del USUARIO, nunca el del proyecto. Y nunca el cwd.

        El cwd de un MCP por stdio no es el repo que uno cree: lo hereda de
        quien lo lanzo. Medido el 2026-09-07, un mismo MCP registrado UNA vez
        corria con el cwd puesto en tres repos ajenos y dejo archivos crudos con
        credenciales en los tres; el `.gitignore` que lo protegia vivia en su
        propio repo mientras el archivo caia en cualquier otro.

        No se arregla ensanchando `.gitignore`: eso cubre los repos que uno
        conoce y deja pasar el proximo. Tampoco atajando el `%TEMP%`, que ataja
        el caso que hace ruido y deja pasar el que hace daño.

        Una ruta explicita en la variable sigue mandando: el default protege al
        que no eligio, no le saca la eleccion al que si.
        """
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME")
        raiz = Path(base) if base else Path.home() / ".local" / "state"
        destino = raiz / self.nombre / _DIRECTORIO
        try:
            destino.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Mejor el cwd que perder el registro: el nombre del archivo avisa
            # igual, y auditar no puede romper nada.
            return Path.cwd()
        return destino

    def ruta(self) -> Path | None:
        """Donde escribe ESTE proceso, o None si el registro esta apagado.

        El nombre del MCP y la marca de crudo van SIEMPRE, incluso con una ruta
        explicita: quien escribio y que esta sin redactar son dos cosas, y las
        dos se leen de un vistazo en un `ls`. Si la ruta configurada ya nombra
        al MCP, no se repite.
        """
        cual = self.modo()
        if cual == "apagado":
            return None
        valor = os.environ.get(self.variable, "").strip()
        if cual == "crudo" or valor in _PALABRAS_REDACTADO:
            base = self.directorio_por_defecto() / _ARCHIVO_POR_DEFECTO
        else:
            base = Path(valor)
            if base.is_dir():
                base = base / _ARCHIVO_POR_DEFECTO
        sufijo = base.suffix or ".jsonl"
        marca = "CRUDA-" if cual == "crudo" else ""
        raiz = base.stem
        if self.nombre not in raiz:
            raiz = f"{self.nombre}-{raiz}"
        return base.with_name(f"{raiz}-{marca}{identidad.escritor()}{sufijo}")

    # -- lo que se escribe --------------------------------------------------

    def _cabecera(self, modo: str) -> Dict[str, Any]:
        """Donde el registro declara su alcance. Primera linea, no al arrancar.

        Se escribe con la PRIMERA llamada: un servidor que nadie uso no deja
        rastro. Y lleva la huella del `auditoria.toml` vigente porque sin ella,
        leyendo el archivo tres semanas despues, un argumento recortado no se
        distingue de uno completo.
        """
        sesion = identidad.get_sesion()
        return {
            "tipo": "cabecera",
            "esquema": ESQUEMA,
            "cuando": datetime.now(timezone.utc).isoformat(),
            "mcp": {"nombre": self.nombre, "version": self.version, "commit": self.commit},
            "pid": sesion["pid"],
            "sesion": sesion["id"],
            "arnes": sesion["arnes"],
            "transporte": self.transporte,
            "framework": self.framework,
            "modo": modo,
            "config": self.redaccion.huella_config,
            "config_problema": self.redaccion.problema,
            "inicio": sesion["iniciada"],
            "cwd": sesion["cwd"],
        }

    def _avisar_una_vez_del_modo_crudo(self, ruta: Path) -> None:
        """Que quede dicho en el log del proceso, no solo en el archivo.

        Es una vez por proceso y nadie mira el log, asi que esto no alcanza: lo
        que de verdad lo recuerda es el acumulado del `estado()`.
        """
        if self._aviso_crudo_dado:
            return
        self._aviso_crudo_dado = True
        logger.warning(
            "AUDITORIA EN MODO CRUDO: %s va a contener argumentos y respuestas SIN "
            "redactar, incluidas credenciales de equipos y lo que se tipee en una "
            "consola. Es para depurar: borralo al terminar y no lo compartas.",
            ruta,
        )

    def registrar(
        self,
        herramienta: str,
        argumentos: Mapping[str, Any] | None = None,
        *,
        resultado: str = "ok",
        duracion_ms: int | None = None,
        error: str | None = None,
        envoltorio: str | None = None,
        retorno: Dict[str, Any] | None = None,
        respuesta: str | None = None,
    ) -> None:
        """Escribe una linea. Nunca levanta: auditar no puede romper.

        `respuesta` se ignora salvo en modo crudo. Ahi es la mitad util: ver el
        argumento que se mando Y lo que el servidor contesto en la MISMA linea
        es lo que permite descubrir que un parametro llego y se descarto en
        silencio. Separados no se cruzan.
        """
        ruta = self.ruta()
        if ruta is None:
            return
        cual = self.modo()
        crudo = cual == "crudo"
        if crudo:
            self._avisar_una_vez_del_modo_crudo(ruta)
        sesion = identidad.get_sesion()
        linea: Dict[str, Any] = {
            "cuando": datetime.now(timezone.utc).isoformat(),
            "sesion": sesion["id"],
            "pid": sesion["pid"],
            "arnes": sesion["arnes"],
            "cliente": (sesion["cliente"] or {}).get("name"),
            "herramienta": herramienta,
            "argumentos": (
                dict(argumentos or {})
                if crudo
                else self.redaccion.argumentos_de(herramienta, argumentos)
            ),
            "resultado": resultado,
            "modo": cual,
        }
        if crudo and respuesta is not None:
            # La marca viaja con el contenido: si alguien pega una linea suelta
            # en otro lado, `modo: crudo` dice que puede traer secretos.
            recortada = respuesta[:MAX_RESPUESTA]
            linea["respuesta"] = recortada
            if len(respuesta) > MAX_RESPUESTA:
                linea["respuesta_recortada_de"] = len(respuesta)
        if duracion_ms is not None:
            linea["duracion_ms"] = duracion_ms
        if error:
            linea["error"] = error
        if envoltorio:
            linea["envoltorio"] = envoltorio
        if retorno:
            # NO contradice a `resultado`: ese habla de la LLAMADA, esto de las
            # operaciones de adentro. Un lote con tres fallos de quince es una
            # llamada que salio bien y tres cosas que no.
            linea["retorno"] = retorno
        self._escribir(ruta, linea, cual)

    def _escribir(self, ruta: Path, linea: Dict[str, Any], modo: str) -> None:
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            # Con el candado tomado: varios hilos del mismo proceso no pueden
            # partirse una linea entre ellos.
            with self._candado, ruta.open("a", encoding="utf-8") as f:
                if ruta not in self._cabecera_escrita:
                    self._cabecera_escrita.add(ruta)
                    f.write(
                        json.dumps(self._cabecera(modo), ensure_ascii=False, default=str) + "\n"
                    )
                f.write(json.dumps(linea, ensure_ascii=False, default=str) + "\n")
        except Exception as fallo:
            logger.warning("No se pudo escribir la auditoria en %s: %s", ruta, fallo)

    # -- el bloque del `check` ---------------------------------------------

    def estado(self) -> Dict[str, Any]:
        """Como esta la auditoria, para el `check` que el MCP ya tiene.

        Va ahi y no en una herramienta nueva: una dedicada a "como esta la
        auditoria" no la llama nadie, que es justo por lo que el problema
        existia. El `check` es el unico lugar donde alguien mira por OTRA razon.

        `acumulado` cuenta el DIRECTORIO y no el archivo propio, porque la
        pregunta que importa es la del que se olvido de apagarlo hace tres dias.
        Medido: once archivos crudos y 44 KB en un dia sin que nadie lo notara,
        horas despues de borrar quince.
        """
        cual = self.modo()
        ruta = self.ruta()
        info: Dict[str, Any] = {"modo": cual, "archivo": str(ruta) if ruta else None}
        if cual == "apagado":
            return info
        if cual == "crudo":
            info["aviso"] = (
                "SIN REDACTAR: este archivo contiene credenciales de equipos y lo "
                "que se tipee en una consola. Es para depurar: borralo al terminar "
                "y no lo compartas."
            )
        try:
            directorio = ruta.parent
            archivos = sorted(directorio.glob("*auditoria-*.jsonl"))
            crudos = [a for a in archivos if "CRUDA-" in a.name]
            edades = [a.stat().st_mtime for a in archivos]
            info["acumulado"] = {
                "directorio": str(directorio),
                "archivos": len(archivos),
                "crudos": len(crudos),
                "bytes": sum(a.stat().st_size for a in archivos),
                "mas_viejo": (
                    datetime.fromtimestamp(min(edades), timezone.utc).isoformat()
                    if edades
                    else None
                ),
            }
        except OSError as error:
            # Que la cuenta falle no puede tumbar un `check`, que es lo que uno
            # usa JUSTO cuando algo anda mal.
            info["acumulado"] = {"error": type(error).__name__}
        return info

"""El registro: donde escribe, como se llama el archivo, y que lleva cada linea.

Nada de aca puede romper una llamada ni el arranque. Un fallo al auditar que
tumbe la operacion convierte una mejora en un modo de fallo nuevo, asi que todo
lo que puede fallar se avisa por el log del proceso y sigue.
"""

import json
import logging
import os
import threading
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lucky_auditoria import identidad
from lucky_auditoria.redaccion import Redaccion, cargar

logger = logging.getLogger(__name__)

# Version del esquema de las lineas. Va en la cabecera: un lector que encuentra
# un numero que no conoce puede decirlo en vez de leer mal.
ESQUEMA = 1

_ARCHIVO_POR_DEFECTO = "auditoria.jsonl"
_DIRECTORIO = "registro_auditoria"

# La herramienta que el propio paquete expone para LEER el registro (R9 bajo
# HTTP). Su llamada se anota -quien leyo el registro es informacion forense de
# primera- pero su retorno NO: leer el registro no puede escribir el registro
# con el registro adentro, porque la segunda lectura traeria la primera y a la
# tercera el archivo crece con copias de si mismo.
#
# Lo decide el paquete y no el `config` del anfitrion. R11 dice que los datos
# son del anfitrion, y esto no es un dato suyo: es una propiedad de esta
# herramienta, y un anfitrion que se olvida de declararla se lleva la recursion
# puesta. Va aca y no en el enganche para que valga en todos a la vez: la
# propiedad, no la mitigacion.
HERRAMIENTA_PROPIA = "auditoria"

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
        self._aviso_sin_proyecto_dado = False

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

        **Solo una ruta ABSOLUTA cuenta como ruta.** Cualquier otro valor apaga
        y lo dice. La version anterior avisaba y escribia igual, que es la mitad
        peor de las dos: un typo o una ruta relativa se volvia un archivo
        colgado del cwd -o sea, del repo de quien lanzo el proceso-, que es
        exactamente el daño que el directorio por defecto vino a evitar. Un
        aviso que no cambia lo que pasa no es una proteccion, es una nota.

        La consecuencia es deliberada: "crudo en una ruta elegida" queda
        inexpresable. Un valor, una decision.
        """
        valor = os.environ.get(self.variable, "").strip()
        if valor.lower() in _PALABRAS_CRUDAS:
            return "crudo"
        if valor in _PALABRAS_APAGADO:
            return "apagado"
        if valor in _PALABRAS_REDACTADO:
            return "redactado"
        if Path(valor).is_absolute():
            return "redactado"
        if not self._aviso_palabra_rara_dado:
            self._aviso_palabra_rara_dado = True
            logger.warning(
                "%s=%r no es una palabra conocida ni una ruta ABSOLUTA. La "
                "auditoria queda APAGADA: una ruta relativa colgaria el archivo "
                "del directorio de trabajo, que un MCP hereda de quien lo lanzo "
                "y suele ser el repo de otro. Las palabras son: %s; o una ruta "
                "absoluta.",
                self.variable,
                valor,
                ", ".join(sorted(_PALABRAS_CRUDAS | _PALABRAS_REDACTADO)),
            )
        return "apagado"

    # -- donde escribe ------------------------------------------------------

    def _destino(self, crudo: bool) -> Path | None:
        """Donde va el registro, o None si no hay donde y hay que apagarse.

        | transporte | modo   | donde                                       |
        |------------|--------|---------------------------------------------|
        | stdio      | ambos  | `<CLAUDE_PROJECT_DIR>/registro_auditoria/`  |
        | stdio      | sin proyecto | APAGADO, con un aviso por proceso     |
        | http       | ambos  | `./registro_auditoria/` del servicio        |

        UNA carpeta por proyecto, sea cual sea el modo. Es una decision del
        humano, cerrada: se ubica por proyecto y se limpia por proyecto, y los
        argumentos tecnicos se resuelven adentro de ella.

        La version anterior de este paquete mandaba el CRUDO al estado del
        usuario, porque un `.gitignore` lo respeta git y nadie mas -un zip, un
        `COPY .`, un sdist copian el arbol entero-. El precio era peor que el
        riesgo: el crudo terminaba en un arbol que no es de ningun proyecto, y
        el que lo dejo prendido tenia que acordarse de que existe ese arbol para
        ir a borrarlo. Nadie se acuerda. Ahora los dos modos estan en la carpeta
        del proyecto, la carpeta se autoprotege, y lo que el `.gitignore` no
        cubre lo cubre la RETENCION (R7): el crudo no vive mas que la sesion de
        depuracion, el `check` dice cuantos hay, y `auditoria limpiar` los borra
        desde donde uno ya esta mirando.

        Sin proyecto no se escribe en ningun lado. Es la diferencia con la
        version anterior, que tenia `_sin_proyecto` bajo el estado del usuario:
        una carpeta que nadie sabia que existia acumulando lo que nadie iba a
        buscar. No escribir tampoco rompe.

        Bajo HTTP el cwd SI se usa, y es lo correcto: el servidor es un
        contenedor de larga vida, su directorio de trabajo es suyo y no lo
        heredo de nadie. Bajo stdio el cwd no se usa nunca -medido: un mismo MCP
        registrado una vez corria con el cwd puesto en tres repos distintos-.
        """
        if self.transporte != "stdio":
            # El proyecto que llamo va como campo de la linea, no en la ruta.
            return Path.cwd() / _DIRECTORIO
        proyecto = identidad.raiz_del_proyecto()
        if not proyecto:
            if not self._aviso_sin_proyecto_dado:
                self._aviso_sin_proyecto_dado = True
                logger.warning(
                    "AUDITORIA APAGADA: ni el arnes ni los roots del cliente "
                    "dijeron cual espacio de trabajo llamo, y el cwd no sirve "
                    "para adivinarlo. No se escribe en ningun otro lado a "
                    "proposito: un registro en un arbol que no es de nadie es "
                    "uno que nadie va a encontrar para borrar."
                )
            return None
        return Path(proyecto) / _DIRECTORIO

    def directorio_por_defecto(self) -> Path | None:
        """El directorio donde va el registro, creado y protegido, o None.

        Que celda de la tabla aplica lo decide `_destino`. Aca queda lo comun:
        crear, autoignorar la primera vez, y no caer a ningun lado si no se
        puede -no escribir tampoco rompe, porque el escritor ya se traga sus
        fallos, y el cwd no se usa nunca.
        """
        destino = self._destino(self.modo() == "crudo")
        if destino is None:
            return None
        try:
            nueva = not destino.exists()
            destino.mkdir(parents=True, exist_ok=True)
            if nueva:
                self._autoignorar(destino)
        except OSError as fallo:
            logger.warning(
                "AUDITORIA APAGADA: no se pudo crear %s (%s). No se escribe en "
                "ningun otro lado a proposito.",
                destino,
                type(fallo).__name__,
            )
            return None
        return destino

    def _autoignorar(self, destino: Path) -> None:
        """Un `.gitignore` con `*` adentro, la primera vez que se crea.

        Es lo que hace posible escribir en el repo de otro sin arruinarlo: la
        carpeta se protege sola y no depende de que ese repo la haya previsto.
        Ensanchar el `.gitignore` de cada repo arregla los que uno conoce; esto
        arregla el proximo.

        El motivo medido (2026-09-07): un mismo MCP registrado UNA vez dejo
        273 KB de crudos con credenciales en tres repos cuyos `.gitignore` no lo
        cubrian. En uno se salvo de casualidad, porque ese repo tenia un patron
        parecido por su propia auditoria.

        No levanta: si no se puede escribir, se avisa fuerte y el registro sigue
        -pero eso ya es una carpeta desprotegida, y hay que verlo.
        """
        marca = destino / ".gitignore"
        try:
            if not marca.exists():
                marca.write_text(
                    "# Escrito por lucky-auditoria-mcp al crear esta carpeta.\n"
                    "# El registro puede contener credenciales: no se commitea.\n"
                    "*\n",
                    encoding="utf-8",
                )
        except OSError as fallo:
            logger.warning(
                "AUDITORIA: no se pudo escribir %s (%s). La carpeta queda SIN "
                "proteger y un `git add -A` de ese repo la levantaria.",
                marca,
                type(fallo).__name__,
            )

    def ruta(self) -> Path | None:
        """Donde escribe ESTE proceso, o None si el registro esta apagado.

        El nombre del MCP y la marca de crudo van SIEMPRE, incluso con una ruta
        elegida: quien escribio y que esta sin redactar son dos cosas, y las dos
        se leen de un vistazo en un `ls`. Si la ruta configurada ya nombra al
        MCP, no se repite.
        """
        cual = self.modo()
        if cual == "apagado":
            return None
        valor = os.environ.get(self.variable, "").strip()
        if cual == "crudo" or valor in _PALABRAS_REDACTADO:
            directorio = self.directorio_por_defecto()
            if directorio is None:
                return None
            base = directorio / _ARCHIVO_POR_DEFECTO
        else:
            # Ya se sabe absoluta: `modo()` apago todo lo demas.
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

    def _cabecera(self, modo: str) -> dict[str, Any]:
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
            # `valida` aparte de `huella` y no deducible de ella: una redaccion
            # cerrada tiene `huella: null`, y "no hay huella" se lee igual que
            # "no la pude calcular". El que lee el archivo tres semanas despues
            # necesita saber si las listas REGIAN, no solo cuales eran.
            "redaccion": {
                "huella": self.redaccion.huella_config,
                "valida": self.redaccion.problema is None,
                "problema": self.redaccion.problema,
            },
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
        retorno: dict[str, Any] | None = None,
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
        if herramienta == HERRAMIENTA_PROPIA:
            retorno = None
            respuesta = None
        cual = self.modo()
        crudo = cual == "crudo"
        if crudo:
            self._avisar_una_vez_del_modo_crudo(ruta)
        sesion = identidad.get_sesion()
        linea: dict[str, Any] = {
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

    def _escribir(self, ruta: Path, linea: dict[str, Any], modo: str) -> None:
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

    def estado(self) -> dict[str, Any]:
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
        info: dict[str, Any] = {"modo": cual, "archivo": str(ruta) if ruta else None}
        # Siempre, no solo cuando hay problema. Una clave que aparece nada mas
        # cuando algo anda mal obliga a saber que puede aparecer: quien lee el
        # `check` sano no se entera de que existe, y entonces tampoco la busca.
        # Una redaccion cerrada no rompe nada -el registro sigue escribiendo,
        # forma y ningun valor- pero apaga el tercer camino de error sin apagar
        # el registro: `rechazos` devuelve vacio sobre un registro con fallos
        # adentro. El ERROR del arranque es una vez, y nadie mira el log.
        info["redaccion"] = "cerrada" if self.redaccion.problema else "abierta"
        if self.redaccion.problema:
            info["redaccion_motivo"] = self.redaccion.problema
        if cual == "apagado":
            return info
        if ruta is None:
            # El interruptor esta PUESTO y no hay donde escribir: desde R1 de
            # 1.5.0, sin proyecto no se escribe en ningun lado. Es un estado
            # legitimo -no escribir tampoco rompe- y el `check` tiene que
            # decirlo, no reventar: hasta 0.5.1 reventaba con un `AttributeError`
            # sobre `ruta.parent`, justo en la herramienta que uno usa CUANDO
            # algo anda mal. Lo encontro un anfitrion con el interruptor
            # encendido corriendo sin `CLAUDE_PROJECT_DIR`.
            info["archivo"] = None
            info["motivo"] = (
                "el interruptor esta puesto pero no hay donde escribir: no se "
                "pudo determinar el proyecto que llamo, y no se escribe en "
                "ningun otro lado a proposito"
            )
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

"""Leer el registro desde el cliente, cuando el archivo vive en otra maquina.

Bajo stdio el registro queda en el disco del que llamo y se lee con `cat` o con
el CLI del paquete. Bajo HTTP no: el archivo vive DENTRO del contenedor, sobre
un volumen persistente, y sin una herramienta que lo exponga **nadie del lado
del cliente lo ve**. Un registro que nadie puede leer es un registro que no
existe.

Son los mismos lectores de R9 -`cazar`, `rechazos`, `por-sesion`- mas lo que
hace falta para alcanzarlos desde afuera: `estado`, `listar` y `leer`.

## Los tres limites, y por que cada uno

Exponer el registro por una herramienta lo pone al alcance de cualquier cliente
conectado, asi que la herramienta tiene que ser mas angosta que el archivo:

1. **Solo el REDACTADO.** El crudo lleva credenciales enteras y se lee en el
   servidor, a mano, por quien tiene acceso a la maquina. No sale por una
   herramienta jamas. Y no alcanza con filtrar por el nombre del archivo: si
   una linea dice `modo: crudo`, se descarta igual y se DICE cuantas -callarlo
   dejaria a la herramienta afirmando que devolvio todo.
2. **Su retorno es opaco para el registro.** Leer el registro no puede escribir
   el registro con el registro adentro: la segunda lectura traeria la primera,
   y a la tercera el archivo crece con copias de si mismo. La llamada SI se
   anota -quien leyo el registro es informacion forense de primera- pero su
   retorno no. Esto lo decide el paquete y no el `config` del anfitrion: un
   anfitrion que se olvida de declararlo se lleva la recursion puesta, y eso no
   es un dato suyo, es una propiedad de esta herramienta.
3. **Pagina con tope declarado.** Devuelve cuantas lineas quedaron afuera. Un
   lector que recorta en silencio es la familia de defectos que este registro
   vino a cazar; cometerla aca seria el peor lugar.
"""

import json
from pathlib import Path
from typing import Any

from lucky_auditoria import lectores
from lucky_auditoria.registro import HERRAMIENTA_PROPIA, Auditor

# El nombre con el que se registra, y el que el registro trata como opaco en el
# retorno. Uno solo, para que no puedan divergir.
NOMBRE = HERRAMIENTA_PROPIA

# Tope por pagina. Alto para que sirva, finito para que nunca devuelva un
# archivo entero de un saque.
TOPE = 200
TOPE_MAXIMO = 1000

ACCIONES = ("estado", "listar", "leer", "cazar", "rechazos", "por_sesion")


class Lector:
    """Los lectores de R9 sobre los archivos REDACTADOS de un auditor.

    Sin framework a proposito: se prueba en proceso, y el enganche de cada SDK
    solo lo envuelve. Lo que se puede probar sin transporte, se prueba sin
    transporte.
    """

    def __init__(self, auditor: Auditor) -> None:
        self.auditor = auditor

    # -- que archivos se pueden mirar ---------------------------------------

    def _directorio(self) -> Path | None:
        ruta = self.auditor.ruta()
        return ruta.parent if ruta else None

    def archivos(self) -> list[Path]:
        """Los redactados del directorio. Los crudos no se listan siquiera.

        No aparecen ni por nombre: decir "hay tres archivos que no te voy a
        mostrar" ya cuenta cuantas sesiones de depuracion hubo. El `estado` de
        R8 SI los cuenta, pero ese lo lee el operador en su propio `check`.
        """
        directorio = self._directorio()
        if directorio is None:
            return []
        try:
            return sorted(
                a
                for a in directorio.glob("*auditoria-*.jsonl")
                if "CRUDA-" not in a.name
            )
        except OSError:
            return []

    def _lineas(self) -> tuple[list[dict], int]:
        """Las lineas redactadas, y cuantas se descartaron por venir en crudo.

        La segunda mitad importa: un archivo con nombre de redactado que trae
        lineas crudas es un problema, y silenciarlo lo esconde justo donde se
        lo estaba buscando.
        """
        limpias, crudas = [], 0
        for linea in lectores.leer(self.archivos()):
            if linea.get("modo") == "crudo":
                crudas += 1
                continue
            limpias.append(linea)
        return limpias, crudas

    # -- las acciones -------------------------------------------------------

    def estado(self) -> dict[str, Any]:
        """Lo mismo que publica el `check` (R8), mas que archivos hay."""
        info = dict(self.auditor.estado())
        info["legibles"] = [a.name for a in self.archivos()]
        return info

    def listar(self) -> dict[str, Any]:
        directorio = self._directorio()
        archivos = []
        for a in self.archivos():
            try:
                archivos.append({"nombre": a.name, "bytes": a.stat().st_size})
            except OSError:
                archivos.append({"nombre": a.name, "bytes": None})
        return {"directorio": str(directorio) if directorio else None, "archivos": archivos}

    def leer(
        self,
        *,
        sesion: str | None = None,
        herramienta: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        limite: int = TOPE,
        salteo: int = 0,
    ) -> dict[str, Any]:
        """Las lineas que pasan el filtro, paginadas y diciendo que quedo afuera.

        `desde` y `hasta` son ISO 8601 y se comparan como texto: el formato de
        `cuando` es UTC con ancho fijo, asi que el orden lexicografico ES el
        cronologico. Compararlos como fechas obligaria a parsear cada linea
        para nada.
        """
        limite = max(1, min(int(limite), TOPE_MAXIMO))
        salteo = max(0, int(salteo))
        lineas, crudas = self._lineas()
        if sesion:
            lineas = [x for x in lineas if x.get("sesion") == sesion]
        if herramienta:
            lineas = [x for x in lineas if x.get("herramienta") == herramienta]
        if desde:
            lineas = [x for x in lineas if (x.get("cuando") or "") >= desde]
        if hasta:
            lineas = [x for x in lineas if (x.get("cuando") or "") <= hasta]
        total = len(lineas)
        pagina = lineas[salteo : salteo + limite]
        return {
            "lineas": pagina,
            "devueltas": len(pagina),
            "total": total,
            # Nunca en silencio: el que pide 200 de 5000 tiene que saberlo sin
            # tener que restarlo el mismo.
            "quedaron_afuera": max(0, total - salteo - len(pagina)),
            "siguiente_salteo": (
                salteo + len(pagina) if salteo + len(pagina) < total else None
            ),
            "omitidas_por_crudas": crudas,
        }

    def cazar(self) -> dict[str, Any]:
        """Siempre vacio por diseño, y lo dice en vez de mentir.

        `cazar` compara el argumento contra la respuesta ENTERA, y la respuesta
        entera solo esta en el registro crudo -que esta herramienta no puede
        leer, por el limite 1. Devolver `[]` a secas se leeria como "no hay
        nada que cazar", que es una afirmacion que esta herramienta no puede
        hacer. Se dice por que.
        """
        return {
            "candidatos": [],
            "aviso": (
                "`cazar` necesita la respuesta entera, que solo existe en el "
                "registro CRUDO. El crudo no sale por esta herramienta: se lee "
                "en el servidor, con `lucky-auditoria cazar <archivo>`."
            ),
        }

    def rechazos(self) -> dict[str, Any]:
        lineas, crudas = self._lineas()
        encontrados = lectores.rechazos(lineas)
        return {
            "rechazos": encontrados[:TOPE],
            "total": len(encontrados),
            "quedaron_afuera": max(0, len(encontrados) - TOPE),
            "omitidas_por_crudas": crudas,
        }

    def por_sesion(self) -> dict[str, Any]:
        lineas, crudas = self._lineas()
        return {"sesiones": lectores.por_sesion(lineas), "omitidas_por_crudas": crudas}

    # -- el despacho --------------------------------------------------------

    def __call__(self, action: str, **filtros: Any) -> str:
        """Una sola herramienta con `action`, como el resto de la casa."""
        if action not in ACCIONES:
            return json.dumps(
                {
                    "error_code": "ACCION_DESCONOCIDA",
                    "acciones": list(ACCIONES),
                },
                ensure_ascii=False,
            )
        if action == "leer":
            salida = self.leer(**filtros)
        else:
            salida = getattr(self, action)()
        return json.dumps(salida, ensure_ascii=False, default=str)


def instalar(servidor: Any, auditor: Auditor, *, nombre: str = NOMBRE) -> Lector:
    """Registra la herramienta en el servidor. Solo tiene sentido bajo HTTP.

    Bajo stdio el archivo esta en el disco del que llamo y `cat` alcanza: sumar
    una herramienta seria agrandar la superficie del MCP para no resolver nada.
    Por eso no se instala sola desde `instalar_auditoria`: la decide el
    anfitrion, que es el que sabe por donde lo sirve.
    """
    lector = Lector(auditor)

    async def auditoria(
        action: str,
        sesion: str | None = None,
        herramienta: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        limite: int = TOPE,
        salteo: int = 0,
    ) -> str:
        """Lee el registro de auditoria de este servidor.

        Solo el registro REDACTADO: el crudo se lee en el servidor y no sale
        por aca. Devuelve paginas, diciendo cuantas lineas quedaron afuera.

        Args:
            action: estado | listar | leer | cazar | rechazos | por_sesion
            sesion: filtra por id de sesion (solo en `leer`)
            herramienta: filtra por nombre de herramienta (solo en `leer`)
            desde, hasta: rango ISO 8601 UTC (solo en `leer`)
            limite: cuantas lineas por pagina (solo en `leer`)
            salteo: desde cual arrancar (solo en `leer`)
        """
        if action == "leer":
            return lector(
                action,
                sesion=sesion,
                herramienta=herramienta,
                desde=desde,
                hasta=hasta,
                limite=limite,
                salteo=salteo,
            )
        return lector(action)

    auditoria.__name__ = nombre
    servidor.tool(name=nombre)(auditoria)
    return lector

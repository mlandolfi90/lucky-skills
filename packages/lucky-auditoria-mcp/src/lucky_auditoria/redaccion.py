"""Que se escribe y que no. Lista blanca, por forma, y una por superficie.

Una lista negra protege lo que uno se acordo de prohibir; una lista blanca
protege lo que uno todavia no invento. Y no alcanza con el NOMBRE: el tipo lo
elige el cliente, y el registro anota ANTES de que nadie valide, asi que
`lineas="<secreto>"` donde se esperaba un entero llega al disco si la lista solo
mira el nombre. Por eso cada campo declara `tipo` y `largo_max`, y lo que no
coincide con la forma declarada cae a descripcion (`{tipo, largo}`), sin valor.

## Los datos son del anfitrion, no del paquete

Las listas viven en el `config/auditoria.toml` del MCP que audita, nunca aca. Si
el paquete trajera las suyas, el primer MCP que sume una herramienta con un
argumento nuevo tendria que tocar el paquete de todos. El paquete lleva el
motor; cada repo lleva sus datos.

## Falla cerrado, sin romper el arranque

Ante cualquier problema -archivo ausente, TOML invalido, una clave que no se
entiende- la redaccion queda VACIA: no se escribe el valor de nada. Es lo
opuesto a lo que sale por descuido, que es una lista escrita y sin efecto. El
caso con nombre: un `por_defecto = "completo"` mal puesto deja el archivo con
pinta de configurado y el registro copiando todo. Aca no hay `por_defecto`, y
un problema se grita por el log ademas de cerrar la puerta.
"""

import hashlib
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:  # 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depende de la version
    import tomli as tomllib  # type: ignore[no-redef]

_ESCALARES = {"str": str, "int": int, "float": float, "bool": bool}

#: Contenedores. Se declaran igual que un escalar, y por omision se anotan como
#: `{tipo, largo}` -o sea, lo mismo que antes de que existieran-. Lo que cambia
#: es que ahora se PUEDEN declarar: antes un `tipo = "list"` no degradaba ese
#: campo, cerraba la redaccion entera, y el anfitrion se quedaba sin forma de
#: expresar "este de acá lo quiero".
_CONTENEDORES = {"list": list, "dict": dict}

_TIPOS = {**_ESCALARES, **_CONTENEDORES}
_LARGO_POR_DEFECTO = 256

#: Cuantos elementos de un contenedor se anotan enteros antes de rendirse y
#: describirlo. Lo mismo que `largo_max` hace con una cadena: un tope existe
#: para que una linea del registro no se coma el archivo.
_ELEMENTOS_POR_DEFECTO = 200

#: Que hacer con lo que hay ADENTRO de un contenedor declarado.
#:
#: `forma` es el defecto y es deliberado: una lista blanca por NOMBRE no puede
#: responder por contenido anidado -el nombre `operations` no dice nada de lo
#: que el llamador metio en `operations[0]["datos"]["custom_fields"]`-, asi que
#: abrirlo tiene que ser una decision escrita del anfitrion y no algo que se
#: hereda por declarar el tipo.
#:
#: `completo` la toma: anota el contenedor entero. Existe porque hay MCP cuya
#: unica pregunta interesante vive adentro de un contenedor -en un MCP de
#: escritura, `operations` ES la intencion, y sin el el registro dice "alguien
#: planifico una operacion"-. El precio es que lo anidado no pasa por ninguna
#: lista blanca. Quien lo escribe lo esta aceptando, y el diff lo muestra.
_CONTENIDOS = ("forma", "completo")


class Redaccion:
    """Las reglas del anfitrion, ya validadas. Inmutable despues de construida."""

    def __init__(
        self,
        *,
        argumentos: Mapping[str, Mapping[str, Any]] | None = None,
        opacas: frozenset = frozenset(),
        huellas: frozenset = frozenset(),
        retorno: Mapping[str, str] | None = None,
        conteos: Mapping[str, Mapping[str, str]] | None = None,
        huella_config: str | None = None,
        problema: str | None = None,
    ) -> None:
        self.argumentos = dict(argumentos or {})
        self.opacas = opacas
        self.huellas = huellas
        self.retorno = dict(retorno or {})
        self.conteos = {k: dict(v) for k, v in (conteos or {}).items()}
        self.huella_config = huella_config
        self.problema = problema

    @classmethod
    def cerrada(cls, problema: str) -> "Redaccion":
        """Nada declarado seguro. Es el estado ante cualquier duda."""
        logger.error(
            "AUDITORIA: no se pudo leer la configuracion de redaccion (%s). "
            "Se registra la FORMA de los argumentos y ningun valor. Revisar "
            "config/auditoria.toml.",
            problema,
        )
        return cls(problema=problema)

    # -- lo que se aplica ---------------------------------------------------

    def describir(self, valor: Any) -> dict[str, Any]:
        """Un argumento no seguro, sin su valor: que forma tenia y cuanto media."""
        forma: dict[str, Any] = {"tipo": type(valor).__name__}
        try:
            forma["largo"] = len(valor)
        except TypeError:
            pass
        return forma

    def _valor_seguro(self, clave: str, valor: Any) -> Any:
        """El valor entero solo si coincide con la forma DECLARADA para esa clave.

        El `bool` se compara aparte porque en Python es una subclase de `int`:
        sin eso, un campo declarado `int` aceptaria un `True` y viceversa.
        """
        regla = self.argumentos.get(clave)
        if regla is None:
            return self.describir(valor)
        esperado = _TIPOS.get(regla.get("tipo", "str"), str)
        if not isinstance(valor, esperado):
            return self.describir(valor)
        if isinstance(valor, bool) is not (esperado is bool):
            return self.describir(valor)

        if esperado in _CONTENEDORES.values():
            # Declarar el tipo NO abre el contenido: eso lo abre `contenido`.
            if regla.get("contenido", "forma") != "completo":
                return self.describir(valor)
            if len(valor) > regla.get("elementos_max", _ELEMENTOS_POR_DEFECTO):
                return self.describir(valor)
            return valor

        largo = regla.get("largo_max", _LARGO_POR_DEFECTO)
        if isinstance(valor, str) and len(valor) > largo:
            return self.describir(valor)
        return valor

    def huella(self, valor: Any) -> str:
        """sha256 corto: correlaciona una credencial sin guardarla.

        Se aplica en los DOS lados o no correlaciona nada, porque una credencial
        nace en un retorno y se usa en un argumento. Por eso `huellas` es una
        lista de nombres de campo, no una lista por superficie.
        """
        return "sha256:" + hashlib.sha256(str(valor).encode("utf-8")).hexdigest()[:12]

    def argumentos_de(
        self, herramienta: str, argumentos: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        """Los argumentos reducidos a lo que se puede escribir sin filtrar nada."""
        if not argumentos:
            return {}
        if herramienta in self.opacas:
            # Ni los nombres de los campos. En una herramienta de texto libre
            # (ssh, console, http, tftp) el largo de lo tipeado mide una
            # password: son opacas hasta en el tamaño.
            operaciones = argumentos.get("operations")
            return {
                "_opaco": True,
                "operaciones": len(operaciones) if isinstance(operaciones, list) else None,
            }
        limpio: dict[str, Any] = {}
        for clave, valor in argumentos.items():
            if valor is None:
                continue
            if clave in self.huellas:
                limpio[clave] = self.huella(valor)
            else:
                limpio[clave] = self._valor_seguro(clave, valor)
        return limpio

    def retorno_de(self, datos: Any) -> dict[str, Any] | None:
        """Los conteos de un lote, si el retorno es uno. El defecto va AL REVES.

        Un argumento no declarado se anota reducido a forma, porque omitirlo
        dejaria al registro mintiendo sobre lo que se PIDIO. Un retorno no
        declarado no se anota ni en forma, porque anotarlo convertiria el
        registro en una copia del inventario. Misma palabra, decision opuesta
        segun el lado.

        Solo CONTEOS, nunca nombres: "cuantas fallaron" y "cuales fallaron"
        tienen precios de exposicion distintos, y la segunda ya vive en la
        respuesta que el modelo recibe.
        """
        if not isinstance(datos, dict):
            return None
        resumen: dict[str, Any] = {}
        for bloque, campos in self.conteos.items():
            adentro = datos.get(bloque)
            if isinstance(adentro, dict):
                for origen, destino in campos.items():
                    valor = adentro.get(origen)
                    if isinstance(valor, int) and not isinstance(valor, bool):
                        resumen[destino] = valor
        for origen, destino in self.retorno.items():
            valor = datos.get(origen)
            if isinstance(valor, bool):
                continue
            if isinstance(valor, int):
                resumen[destino] = valor
            elif isinstance(valor, list):
                resumen[destino] = len(valor)
        return resumen or None


# -- carga -------------------------------------------------------------------

_CLAVES = {"argumentos", "herramientas", "huellas", "retorno", "conteos"}


def cargar(ruta: Path | str | None) -> Redaccion:
    """Lee el `auditoria.toml` del anfitrion. Ante cualquier duda, cerrada."""
    if ruta is None:
        return Redaccion.cerrada("no se declaro la ruta de config/auditoria.toml")
    camino = Path(ruta)
    try:
        crudo = camino.read_bytes()
    except OSError as e:
        return Redaccion.cerrada(f"no se pudo leer {camino}: {type(e).__name__}")
    try:
        datos = tomllib.loads(crudo.decode("utf-8"))
    except Exception as e:
        return Redaccion.cerrada(f"{camino} no es un TOML valido: {type(e).__name__}")

    donde = ""
    if "auditoria" in datos:
        # El bloque puede vivir como tabla [auditoria] dentro del config.toml
        # unico del anfitrion (estandar de creacion de MCPs, entrega 0001,
        # 2026-09-10): el resto de ese archivo no es asunto de este paquete y
        # puede traer credenciales, asi que ningun mensaje repite contenido:
        # nombres de secciones y claves, nunca valores. Sin la tabla, el
        # archivo entero es suyo, como siempre. Las dos cosas a la vez son una
        # regla que el operador cree escrita y no rige: cerrada.
        bloque = datos["auditoria"]
        if not isinstance(bloque, dict):
            return Redaccion.cerrada(f"{camino}: [auditoria] no es una tabla")
        en_raiz = sorted(set(datos) & _CLAVES)
        if en_raiz:
            return Redaccion.cerrada(
                f"{camino} declara [auditoria] y ademas {en_raiz} en la raiz: "
                "el bloque vive en un solo lugar"
            )
        datos = bloque
        donde = " en [auditoria]"

    sobran = set(datos) - _CLAVES
    if sobran:
        # Una seccion que el paquete no entiende es una regla que el operador
        # cree escrita y no rige. Es exactamente el modo de fallo con nombre.
        return Redaccion.cerrada(
            f"{camino} declara secciones desconocidas{donde}: {sorted(sobran)}"
        )

    try:
        argumentos = {}
        for clave, regla in (datos.get("argumentos") or {}).items():
            if not isinstance(regla, dict) or regla.get("tipo") not in _TIPOS:
                return Redaccion.cerrada(f"el argumento {clave} no declara un tipo valido")
            contenido = regla.get("contenido", "forma")
            if contenido not in _CONTENIDOS:
                return Redaccion.cerrada(
                    f"el argumento {clave} declara contenido={contenido!r}, y solo "
                    f"valen {list(_CONTENIDOS)}"
                )
            if contenido == "completo" and regla["tipo"] not in _CONTENEDORES:
                # En un escalar no significa nada, y un ajuste que no hace nada
                # es peor que ninguno: el operador cree que declaro algo.
                return Redaccion.cerrada(
                    f"el argumento {clave} declara contenido=completo sobre un "
                    f"{regla['tipo']}, que no tiene contenido que abrir"
                )
            argumentos[clave] = regla
        opacas = frozenset((datos.get("herramientas") or {}).get("opacas") or ())
        huellas = frozenset((datos.get("huellas") or {}).get("campos") or ())
        retorno = dict(datos.get("retorno") or {})
        conteos = {k: dict(v) for k, v in (datos.get("conteos") or {}).items()}
    except (AttributeError, TypeError, ValueError) as e:
        return Redaccion.cerrada(f"{camino} tiene una forma inesperada: {type(e).__name__}")

    return Redaccion(
        argumentos=argumentos,
        opacas=opacas,
        huellas=huellas,
        retorno=retorno,
        conteos=conteos,
        # Va en la cabecera: sin el, un argumento recortado no se distingue de
        # uno completo al leer el registro tres semanas despues.
        huella_config="sha256:" + hashlib.sha256(crudo).hexdigest()[:12],
    )

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
        visibles: Mapping[str, frozenset] | None = None,
        huellas: frozenset = frozenset(),
        retorno: Mapping[str, str] | None = None,
        conteos: Mapping[str, Mapping[str, str]] | None = None,
        huella_config: str | None = None,
        problema: str | None = None,
    ) -> None:
        self.argumentos = dict(argumentos or {})
        self.opacas = opacas
        self.visibles = dict(visibles or {})
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
            "Se registra cada llamada con sus argumentos opacos: ni valores, ni "
            "nombres, ni largos. Revisar config/auditoria.toml.",
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
        if self.problema is not None:
            # Con la redaccion CERRADA toda herramienta es opaca (S-26). Hasta
            # 0.9.0 la cerrada solo miraba `opacas`, que queda vacia, y la
            # herramienta de texto libre anotaba sus campos y sus largos: la
            # cerrada salia MENOS privada que la abierta, justo en las que mas
            # importan. Sin conteo de operaciones: cerrada no sabe cual es.
            return {"_opaco": True}
        if herramienta in self.opacas:
            # Ni los nombres de los campos. En una herramienta de texto libre
            # (ssh, console, http, tftp) el largo de lo tipeado mide una
            # password: son opacas hasta en el tamaño.
            operaciones = argumentos.get("operations")
            opaco: dict[str, Any] = {
                "_opaco": True,
                "operaciones": len(operaciones) if isinstance(operaciones, list) else None,
            }
            # Salvo los campos que el anfitrion declaro VISIBLES (W, pedido de
            # lucky-tool-mtk-chr: el `escribe` de `chr_comando_crudo`). Pasan
            # solo si coinciden con su forma declarada en `[argumentos]`; si no,
            # no se anotan ni descritos, porque describir es anotar el largo.
            for campo in sorted(self.visibles.get(herramienta, ())):
                if campo not in argumentos or argumentos[campo] is None:
                    continue
                valor = argumentos[campo]
                if campo in self.huellas:
                    opaco[campo] = self.huella(valor)
                    continue
                seguro = self._valor_seguro(campo, valor)
                if seguro is valor:
                    opaco[campo] = valor
            return opaco
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

# Lo que vale ADENTRO de cada seccion (S-24). Hasta 0.9.0 solo se miraba el
# primer nivel: `opaca` por `opacas` o `largo` por `largo_max` cargaban, y la
# regla que el operador creia escrita no regia.
_CLAVES_DEL_ARGUMENTO = {"tipo", "largo_max", "contenido", "elementos_max"}
_CLAVES_DE_HERRAMIENTAS = {"opacas", "visibles"}
_CLAVES_DE_HUELLAS = {"campos"}


def _es_tope(valor: Any) -> bool:
    """Un entero positivo de verdad. `True` es un `int` en Python y no es un tope."""
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def _lista_de_nombres(valor: Any) -> bool:
    return isinstance(valor, list) and all(isinstance(v, str) for v in valor)


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
            sobran = set(regla) - _CLAVES_DEL_ARGUMENTO
            if sobran:
                return Redaccion.cerrada(
                    f"el argumento {clave} tiene claves desconocidas: {sorted(sobran)}"
                )
            for tope in ("largo_max", "elementos_max"):
                # S-23: un `largo_max = "500"` cargaba, y la primera llamada
                # levantaba `TypeError` al comparar adentro de `registrar`.
                if tope in regla and not _es_tope(regla[tope]):
                    return Redaccion.cerrada(
                        f"el argumento {clave} declara {tope} que no es un entero positivo"
                    )
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

        herramientas = datos.get("herramientas") or {}
        huellas_ = datos.get("huellas") or {}
        for seccion, valida, valor in (
            ("herramientas", _CLAVES_DE_HERRAMIENTAS, herramientas),
            ("huellas", _CLAVES_DE_HUELLAS, huellas_),
        ):
            if not isinstance(valor, dict):
                return Redaccion.cerrada(f"[{seccion}] no es una tabla")
            sobran = set(valor) - valida
            if sobran:
                return Redaccion.cerrada(
                    f"[{seccion}] tiene claves desconocidas: {sorted(sobran)}"
                )
        for seccion, valor in (
            ("herramientas.opacas", herramientas.get("opacas", [])),
            ("huellas.campos", huellas_.get("campos", [])),
        ):
            if not _lista_de_nombres(valor):
                # `opacas = "buscar"` cargaba como un conjunto de LETRAS.
                return Redaccion.cerrada(f"{seccion} no es una lista de nombres")
        opacas = frozenset(herramientas.get("opacas", ()))
        huellas = frozenset(huellas_.get("campos", ()))

        # W: campos que una herramienta opaca deja ver. Cada uno tiene que
        # estar declarado en `[argumentos]` con su forma, y la herramienta tiene
        # que ser opaca: en cualquier otro caso el ajuste no hace nada, y uno
        # que no hace nada es peor que ninguno, porque el operador cree que
        # declaro algo.
        visibles_crudos = herramientas.get("visibles", {})
        if not isinstance(visibles_crudos, dict):
            return Redaccion.cerrada("[herramientas.visibles] no es una tabla")
        visibles = {}
        for herramienta, campos in visibles_crudos.items():
            if not _lista_de_nombres(campos):
                return Redaccion.cerrada(
                    f"[herramientas.visibles] {herramienta} no es una lista de nombres"
                )
            if herramienta not in opacas:
                return Redaccion.cerrada(
                    f"[herramientas.visibles] declara {herramienta}, que no es opaca"
                )
            sin_forma = sorted(c for c in campos if c not in argumentos and c not in huellas)
            if sin_forma:
                return Redaccion.cerrada(
                    f"[herramientas.visibles] {herramienta} deja ver {sin_forma} sin "
                    "declararlos en [argumentos]"
                )
            visibles[herramienta] = frozenset(campos)

        retorno = dict(datos.get("retorno") or {})
        conteos = {k: dict(v) for k, v in (datos.get("conteos") or {}).items()}
        nombres = list(retorno.values()) + [d for v in conteos.values() for d in v.values()]
        if not all(isinstance(n, str) for n in nombres):
            return Redaccion.cerrada("[retorno] y [conteos] nombran sus destinos con texto")
    except (AttributeError, TypeError, ValueError) as e:
        return Redaccion.cerrada(f"{camino} tiene una forma inesperada: {type(e).__name__}")

    return Redaccion(
        argumentos=argumentos,
        opacas=opacas,
        visibles=visibles,
        huellas=huellas,
        retorno=retorno,
        conteos=conteos,
        # Va en la cabecera: sin el, un argumento recortado no se distingue de
        # uno completo al leer el registro tres semanas despues.
        huella_config="sha256:" + hashlib.sha256(crudo).hexdigest()[:12],
    )

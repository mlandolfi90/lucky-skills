"""De donde sale la identidad que el arnes le hereda al proceso hijo.

Un MCP por stdio no se entera de quien lo llamo: el protocolo no lo dice y el
nombre del cliente nombra al PRODUCTO (`claude-code` en todas las sesiones a la
vez). Lo que si llega es el ENTORNO del proceso hijo, porque el arnes se lo
pone al lanzarlo.

Eso es un canal por producto, no un estandar, y por eso se modela como
catalogo: cada arnes declara su variable testigo -la que dice "fui yo el que
lanzo esto"- y las variables de las que saca sus campos. Sumar un arnes no toca
este archivo si viene de afuera (`entry_points`), que es la unica forma que
sobrevive al reparto: el paquete no puede iterar sus propios modulos y llamarlo
extensible, porque entonces extenderlo es tocarlo.

Y EXTENDER uno que ya existe tampoco lo toca: los arneses del anfitrion van
primero en `catalogo()`, asi que declarar uno con el mismo testigo lo reemplaza.
Hasta 0.6.0 iban ultimos y no reemplazaban nada; ver `catalogo()`.

## La lista blanca de variables, y por que existe

El mismo entorno que trae la identidad trae los tokens del arnes. Aca la
declaracion del arnes ES la lista blanca: `campos` nombra una por una las
variables que se leen, y ningun otro codigo del paquete toca `os.environ` para
armar una linea del registro. `prohibidas()` prueba la clase entera -que
ninguna variable declarada, por ningun arnes, presente o futuro, se llame como
un secreto- en vez de revisar caso por caso.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

# Un nombre de variable con cualquiera de estas partes es una credencial. Se
# prueba por clase: la guarda corre sobre TODO arnes registrado, incluido el que
# alguien agregue el año que viene desde otro paquete.
PALABRAS_DE_SECRETO: tuple[str, ...] = (
    "TOKEN",
    "SECRET",
    "KEY",
    "PASSWORD",
    "PASSWD",
    "CREDENTIAL",
    "AUTH",
)


@dataclass(frozen=True)
class Arnes:
    """Un producto que lanza MCP y le hereda algo util al proceso hijo.

    `testigo` es la variable cuya PRESENCIA identifica al arnes; `campos` mapea
    variable de entorno -> nombre del campo en la linea del registro, y es la
    lista blanca completa de lo que se lee.
    """

    id: str
    testigo: str
    campos: Mapping[str, str] = field(default_factory=dict)

    def presente(self, entorno: Mapping[str, str] | None = None) -> bool:
        return bool((entorno if entorno is not None else os.environ).get(self.testigo))

    def leer(self, entorno: Mapping[str, str] | None = None) -> dict[str, Any]:
        fuente = entorno if entorno is not None else os.environ
        datos: dict[str, Any] = {"id": self.id}
        for variable, campo in self.campos.items():
            datos[campo] = fuente.get(variable) or None
        return datos


# Claude Code. Medido el 2026-09-07 sobre procesos vivos con
# `psutil.Process(pid).environ()`: del mismo MCP registrado UNA vez, dos
# procesos tenian el cwd en `%TEMP%` y tres en repos distintos, y
# `CLAUDE_PROJECT_DIR` traia la respuesta que el cwd no daba. Sirve para
# ATRIBUIR -nombra al que invoco- y no para ubicar archivos: un MCP compartido
# tiene N valores a la vez. Por eso el archivo va al directorio del usuario
# (regla R1) y esto va en la linea.
CLAUDE_CODE = Arnes(
    id="claude-code",
    testigo="CLAUDE_CODE_SESSION_ID",
    campos={
        "CLAUDE_CODE_SESSION_ID": "sesion",
        "CLAUDE_PROJECT_DIR": "proyecto",
    },
)

# El arnes que no es ninguno: proceso lanzado a mano, o un producto que todavia
# no esta catalogado. No inventa nada, y su ausencia de testigo lo deja ultimo.
DESCONOCIDO = Arnes(id="desconocido", testigo="", campos={})

_INCORPORADOS: tuple[Arnes, ...] = (CLAUDE_CODE,)
_GRUPO_DE_ENTRADA = "lucky_auditoria.arneses"


def _de_afuera() -> tuple[Arnes, ...]:
    """Los arneses que declara OTRO paquete, por `entry_points`.

    Nunca levanta: un plugin roto no puede impedir que el MCP arranque, y menos
    el modulo que existe para no romper nada.
    """
    from importlib import metadata

    encontrados = []
    try:
        for punto in metadata.entry_points(group=_GRUPO_DE_ENTRADA):
            try:
                valor = punto.load()
            except Exception:
                continue
            for arnes in valor if isinstance(valor, (list, tuple)) else (valor,):
                if isinstance(arnes, Arnes):
                    encontrados.append(arnes)
    except Exception:
        return ()
    return tuple(encontrados)


def catalogo() -> tuple[Arnes, ...]:
    """Todos los arneses conocidos. **Los del anfitrion van primero.**

    El orden importa porque `detectar()` corta en el primero cuyo testigo este
    presente. Con los incorporados adelante, un anfitrion no podia AGREGARLE un
    campo a un arnes que ya existe -declaraba el suyo, el de fabrica contestaba
    primero, y el suyo no corria nunca-. Medido el 2026-09-10 en
    `lucky-tool-netbox`, que quiso sumar `CLAUDE_CODE_ENTRYPOINT` al arnes de
    Claude Code: los tres intentos -mismo testigo, otro testigo, otro id-
    devolvieron el de fabrica.

    Eso contradecia lo que este mismo archivo promete arriba: que sumar un
    arnes no lo toque. Sumar uno nuevo andaba; extender uno existente, no, y es
    el caso que mas se pide, porque los campos utiles de un producto se
    descubren de a uno.

    El precio: un anfitrion puede TAPAR un arnes de fabrica sin querer. Por eso
    `sombras()` lo nombra y `instalar_auditoria` lo avisa una vez al arrancar.
    Tapar es legitimo -es el anfitrion, y es su proceso-; taparlo en silencio
    no, porque lo que cambia es la lista blanca del entorno.
    """
    return _de_afuera() + _INCORPORADOS


def sombras(arneses: tuple[Arnes, ...] | None = None) -> dict[str, str]:
    """Que arnes de fabrica quedo tapado por uno del anfitrion, y por cual.

    Tapado = el de fabrica ya no puede contestar, porque otro con el MISMO
    testigo va antes. Un id repetido con testigo distinto no tapa nada: los dos
    pueden contestar, cada uno cuando le toca su variable.
    """
    delanteros: dict[str, str] = {}
    tapados: dict[str, str] = {}
    for arnes in arneses if arneses is not None else catalogo():
        if not arnes.testigo:
            continue
        if arnes.testigo in delanteros:
            tapados[arnes.id] = delanteros[arnes.testigo]
        else:
            delanteros[arnes.testigo] = arnes.id
    return tapados


def prohibidas(arneses: tuple[Arnes, ...] | None = None) -> dict[str, list]:
    """Las variables declaradas que se llaman como un secreto. Vacio es lo sano.

    La usa la prueba del paquete Y la prueba de cada anfitrion: el que agrega un
    arnes hereda la guarda sin escribirla.
    """
    culpables: dict[str, list] = {}
    for arnes in arneses if arneses is not None else catalogo():
        malas = [
            v
            for v in (*arnes.campos.keys(), arnes.testigo)
            if v and any(p in v.upper() for p in PALABRAS_DE_SECRETO)
        ]
        if malas:
            culpables[arnes.id] = sorted(malas)
    return culpables


def detectar(entorno: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Que arnes lanzo este proceso y que le heredo, o `desconocido`."""
    for arnes in catalogo():
        if arnes.testigo and arnes.presente(entorno):
            return arnes.leer(entorno)
    return DESCONOCIDO.leer(entorno)

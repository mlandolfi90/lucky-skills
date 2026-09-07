"""Cazar, no solo leer. Un formato, unos lectores; si no, cada MCP reinventa el jq.

El registro no se escribe para tenerlo: se escribe para pasarle estas tres
preguntas encima. `cazar` es la que paga el paquete entero.
"""

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


def leer(rutas: Iterable[Path | str]) -> Iterator[dict[str, Any]]:
    """Las lineas de uno o varios registros, salteando la cabecera y la basura.

    Una linea rota no puede cortar la lectura: un registro se lee JUSTO cuando
    algo anduvo mal, y a veces lo que anduvo mal fue el disco.
    """
    for ruta in rutas:
        try:
            with Path(ruta).open(encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                    try:
                        dato = json.loads(linea)
                    except ValueError:
                        continue
                    if isinstance(dato, dict) and dato.get("tipo") != "cabecera":
                        yield dato
        except OSError:
            continue


def _escalares(valor: Any) -> Iterator[Any]:
    """Todo escalar que aparece en la respuesta, a cualquier profundidad."""
    if isinstance(valor, dict):
        for adentro in valor.values():
            yield from _escalares(adentro)
    elif isinstance(valor, list):
        for adentro in valor:
            yield from _escalares(adentro)
    else:
        yield valor


def _respuesta_estructurada(linea: dict[str, Any]) -> Any:
    """La respuesta parseada de una linea cruda, o None.

    Estructurada y no texto: buscar sobre el texto confunde una mencion con un
    valor, y eso ya costo un diagnostico en este mismo repo. Sin la respuesta
    entera no hay contra que comparar, y una respuesta RECORTADA daria falsos
    positivos -por eso tambien se descarta.
    """
    if linea.get("modo") != "crudo":
        return None
    texto = linea.get("respuesta")
    if not texto or linea.get("respuesta_recortada_de"):
        return None
    try:
        return json.loads(texto)
    except (ValueError, TypeError):
        return None


def cazar(lineas: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Argumentos que el cliente mando y que no vuelven en ningun escalar.

    Es la señal mecanizable que sale del registro CRUDO: un parametro que llego
    al servidor y se descarto en silencio se ve asi, porque su valor no aparece
    en ningun lado de la respuesta.

    Produce CANDIDATOS, nunca veredictos. Hay argumentos que legitimamente no
    vuelven -un `confirm_project_id`, un `format`, un `lineas` que acota y no se
    refleja- y decidir cual es cual exigiria conocer cada verbo. Un cazador que
    decidiera solo tendria que conocerlos todos, y seria la misma suposicion que
    esto viene a evitar.

    Tres detalles que importan mas que la señal, los tres medidos por
    lucky-tool-mtk-chr:

    - **Por VALOR, nunca por substring.** Buscar `str(1)` da verdadero contra
      cualquier `1` suelto y la señal se vuelve inutil para enteros. Y un
      `name="R1"` que aparece dentro de "R10" no es el mismo dato: contarlo como
      devuelto taparia justo el caso que se busca.
    - **Se saltean `None` y los booleanos.** Un booleano no "vuelve": cambia el
      camino. Compararlo produce ruido garantizado.
    - **Solo corre si `ok` no es False.** En un rechazo es normal que el
      argumento no haya tenido efecto, asi que ahi la señal no dice nada.
    """
    candidatos = []
    for linea in lineas:
        datos = _respuesta_estructurada(linea)
        if datos is None:
            continue
        if isinstance(datos, dict) and datos.get("ok") is False:
            continue
        vistos = set()
        for escalar in _escalares(datos):
            if isinstance(escalar, bool) or escalar is None:
                continue
            if isinstance(escalar, (str, int, float)):
                vistos.add(escalar)
        for clave, valor in (linea.get("argumentos") or {}).items():
            if valor is None or isinstance(valor, (dict, list, bool)):
                continue
            if valor not in vistos:
                candidatos.append(
                    {
                        "cuando": linea.get("cuando"),
                        "sesion": linea.get("sesion"),
                        "herramienta": linea.get("herramienta"),
                        "argumento": clave,
                    }
                )
    return candidatos


# Claves que nombran una cuenta. Un cero solo es "efecto vacio" en una de
# estas: un `puerto: 0` no es un efecto vacio, es un puerto.
_CLAVES_DE_CONTEO = ("total", "cuantos", "cantidad")

# Umbral ABSOLUTO, no comparado contra otras llamadas al mismo verbo. Comparar
# contra el historial suena mejor y necesitaria un corpus por verbo: ahi ya es
# un modelo, no un lector. La medicion: un parser que no entendio nada deja
# `{"ok": true}` y a lo sumo un campo mas.
_CLAVES_FLACA = 2


def _vacios(respuesta: dict[str, Any]) -> dict[str, Any]:
    """Las claves de primer nivel que volvieron vacias.

    No es recursivo A PROPOSITO: anidado da demasiado ruido y la señal deja de
    servir.
    """
    encontrados: dict[str, Any] = {}
    for clave, valor in respuesta.items():
        if isinstance(valor, list) and not valor:
            encontrados[clave] = []
        elif (
            isinstance(valor, int)
            and not isinstance(valor, bool)
            and valor == 0
            and clave in _CLAVES_DE_CONTEO
        ):
            encontrados[clave] = 0
    return encontrados


def afirmaciones(lineas: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Respuestas que dicen que salio bien y no muestran que haya pasado nada.

    La otra mitad de `cazar`, con las definiciones que midio lucky-tool-mtk-chr
    sobre 39 verbos. Misma familia que todo lo demas: la respuesta afirma mas de
    lo que paso.

    - **exito con efecto vacio**: `ok: true`, hay claves vacias, y TODAS las
      listas del retorno estan vacias. Esa ultima condicion es la que separa la
      señal del ruido: una lista vacia entre cinco llenas es normal.
    - **respuesta flaca**: `ok: true` con dos claves o menos.

    CANDIDATOS, no veredictos, igual que `cazar`. Lo que encontro donde se
    midio: tres defectos de "no fallaba, contestaba mal" -una duracion afirmada
    de 24 h contra un timeout real de 59m58s, un conteo sobre una ventana
    truncada sin decirlo, y 20 de 200 coincidencias sin decirlo. Los tres se
    arreglaron REPORTANDO lo que pasaba, nunca cambiando el comportamiento: en
    el primero, sobrescribir el bloqueo habria dejado que cualquiera lo acorte.
    """
    encontradas = []
    for linea in lineas:
        respuesta = _respuesta_estructurada(linea)
        if not isinstance(respuesta, dict) or respuesta.get("ok") is not True:
            continue
        señales = []
        vacios = _vacios(respuesta)
        listas = [v for v in respuesta.values() if isinstance(v, list)]
        # TODAS las listas vacias, no algunas: una lista vacia entre cinco
        # llenas es normal, y sin esta condicion la señal se vuelve ruido.
        #
        # La formula que me pasaron era `len(vacios) == len(listas)`, y no dice
        # lo mismo que su propio comentario: como `vacios` junta tambien los
        # ceros de las claves de conteo, un `{"ok": true, "hallazgos": [],
        # "total": 0}` -el caso de manual- da 2 contra 1 y NO se marca. Se
        # implementa la intencion declarada, que es la que las tres mediciones
        # respaldan, y la diferencia queda reportada a quien la midio.
        if listas and all(not x for x in listas):
            señales.append("exito_con_efecto_vacio")
        if len(respuesta) <= _CLAVES_FLACA:
            señales.append("respuesta_flaca")
        if señales:
            encontradas.append(
                {
                    "cuando": linea.get("cuando"),
                    "sesion": linea.get("sesion"),
                    "herramienta": linea.get("herramienta"),
                    "señales": señales,
                    "vacios": sorted(vacios),
                }
            )
    return encontradas


def rechazos(lineas: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Llamadas que salieron bien y trajeron el rechazo adentro.

    El tercer camino de la regla 4, y el que ningun framework puede ver: un lote
    con tres fallos de quince es una llamada exitosa y tres cosas que no
    pasaron. Sin esto el registro anota `ok` a secas.
    """
    encontrados = []
    for linea in lineas:
        retorno = linea.get("retorno") or {}
        fallaron = retorno.get("fallaron")
        if isinstance(fallaron, int) and fallaron > 0:
            encontrados.append(
                {
                    "cuando": linea.get("cuando"),
                    "sesion": linea.get("sesion"),
                    "herramienta": linea.get("herramienta"),
                    "resultado": linea.get("resultado"),
                    "retorno": retorno,
                }
            )
    return encontrados


def por_sesion(lineas: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Que hizo cada sesion. La pregunta original, la que motivo todo esto."""
    cuentas: dict[str, dict[str, Any]] = {}
    for linea in lineas:
        sesion = linea.get("sesion") or "?"
        entrada = cuentas.setdefault(
            sesion,
            {
                "llamadas": 0,
                "errores": 0,
                "herramientas": {},
                "proyecto": (linea.get("arnes") or {}).get("proyecto"),
                "desde": linea.get("cuando"),
                "hasta": linea.get("cuando"),
            },
        )
        entrada["llamadas"] += 1
        if linea.get("resultado") == "error":
            entrada["errores"] += 1
        herramienta = linea.get("herramienta") or "?"
        entrada["herramientas"][herramienta] = entrada["herramientas"].get(herramienta, 0) + 1
        cuando = linea.get("cuando")
        if cuando:
            entrada["hasta"] = cuando
    return cuentas

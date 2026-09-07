"""Cazar, no solo leer. Un formato, unos lectores; si no, cada MCP reinventa el jq.

El registro no se escribe para tenerlo: se escribe para pasarle estas tres
preguntas encima. `cazar` es la que paga el paquete entero.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List


def leer(rutas: Iterable[Path | str]) -> Iterator[Dict[str, Any]]:
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


def cazar(lineas: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Argumentos que el cliente mando y que no vuelven en ningun escalar.

    Es la señal mecanizable que sale del registro CRUDO: un parametro que llego
    al servidor y se descarto en silencio se ve asi, porque su valor no aparece
    en ningun lado de la respuesta.

    Produce CANDIDATOS, nunca veredictos. Hay argumentos que legitimamente no
    vuelven -un `confirm_project_id`, un `format`- y decidir cual es cual
    exigiria conocer cada verbo. Se tria a mano.

    La comparacion es por VALOR y no por substring: un `name="R1"` que aparece
    dentro de la palabra "R10" no es el mismo dato, y contarlo como devuelto
    taparia justo el caso que se busca.
    """
    candidatos = []
    for linea in lineas:
        if linea.get("modo") != "crudo":
            # Sin la respuesta entera no hay contra que comparar, y comparar
            # contra una respuesta recortada daria falsos positivos.
            continue
        respuesta = linea.get("respuesta")
        if not respuesta or linea.get("respuesta_recortada_de"):
            continue
        try:
            datos = json.loads(respuesta)
        except (ValueError, TypeError):
            continue
        vistos = set()
        for escalar in _escalares(datos):
            if isinstance(escalar, (str, int, float, bool)):
                vistos.add(escalar)
        for clave, valor in (linea.get("argumentos") or {}).items():
            if isinstance(valor, (dict, list)) or valor is None:
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


def rechazos(lineas: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def por_sesion(lineas: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Que hizo cada sesion. La pregunta original, la que motivo todo esto."""
    cuentas: Dict[str, Dict[str, Any]] = {}
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

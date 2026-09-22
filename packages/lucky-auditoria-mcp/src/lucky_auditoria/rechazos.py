"""Que retorno de una herramienta es un rechazo, y con que codigo se anota.

Es el segundo de los tres caminos, y es estructural: el `is_error` del
framework marca SUS excepciones, no los rechazos del dominio. Un
`{"ok": false}` llega con `is_error=False`, porque ningun framework puede saber
que ese retorno es un error. Creerle anota "ok" sobre el 100% de los rechazos.

Hasta 0.8.0 se reconocia una sola forma, `error_code`. Medido por
lucky-tool-mtk-chr: su pasarela rechaza con `{"ok": false, "<categoria>": true}`
y un verbo que se niega por su cuenta devuelve `ok: false` sin categoria; las
dos quedaban `resultado: "ok"`. Y el lector del propio paquete ya contaba
`ok: false` como fracaso: escritor y lector no coincidian.

Se anota solo el CODIGO, que es un nombre: `error_code` si lo hay; si no, la
categoria booleana que acompana al `ok: false`; si no hay ninguna,
`rechazo_del_verbo`. Nunca el mensaje ni el contexto, que arrastran los
argumentos.
"""

from typing import Any

RECHAZO_SIN_CATEGORIA = "rechazo_del_verbo"


def codigo_de_error(datos: Any) -> str | None:
    """El codigo si la herramienta DEVOLVIO un error en vez de levantarlo."""
    if not isinstance(datos, dict):
        return None
    if datos.get("error_code"):
        return str(datos["error_code"])
    if datos.get("ok") is False:
        for clave, valor in datos.items():
            if clave != "ok" and valor is True:
                return str(clave)
        return RECHAZO_SIN_CATEGORIA
    return None

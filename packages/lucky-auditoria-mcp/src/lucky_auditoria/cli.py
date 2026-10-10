"""`lucky-auditoria <lectura> <archivos...>` — los lectores desde la terminal.

Sale JSON porque el que lee un registro suele estar encadenando otra cosa, y una
tabla linda obliga a re-parsearla.
"""

import argparse
import glob
import json
import sys
from pathlib import Path

from lucky_auditoria import lectores

_LECTURAS = {
    "cazar": lectores.cazar,
    "rechazos": lectores.rechazos,
    "por-sesion": lectores.por_sesion,
    "afirmaciones": lectores.afirmaciones,
}


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lucky-auditoria",
        description="Lee los registros de auditoria de un MCP.",
    )
    parser.add_argument("lectura", choices=sorted(_LECTURAS))
    parser.add_argument(
        "archivos",
        nargs="+",
        help="uno o mas .jsonl; acepta comodines (*.jsonl) en cualquier shell",
    )
    args = parser.parse_args(argv)

    rutas = [Path(r) for a in args.archivos for r in _expandir(a)]
    faltan = [str(r) for r in rutas if not r.is_file()]
    if faltan:
        # Decirlo en vez de devolver una lista vacia: un resultado vacio por
        # archivo inexistente se lee como "no hay nada que reportar".
        print(f"no existen: {', '.join(faltan)}", file=sys.stderr)
        return 2

    salida = _LECTURAS[args.lectura](lectores.leer(rutas))
    texto = json.dumps(salida, ensure_ascii=False, indent=2, default=str) + "\n"
    # Siempre UTF-8 (S-27). Por un pipe en Windows `print` escribe en la pagina
    # de codigos de la consola (cp1252): una `ñ` deja de ser UTF-8, y un
    # caracter que esa pagina no tiene tumba la salida con `UnicodeEncodeError`.
    # Y la clave `señales` de `afirmaciones` lleva una siempre.
    salida_binaria = getattr(sys.stdout, "buffer", None)
    if salida_binaria is not None:
        sys.stdout.flush()
        salida_binaria.write(texto.encode("utf-8"))
        salida_binaria.flush()
    else:
        sys.stdout.write(texto)
    return 0


def _expandir(argumento: str) -> list[str]:
    """Los comodines los expande el CLI, no el shell (S-28).

    Bash los expande antes de llamar; PowerShell y cmd los pasan tal cual, y
    `*.jsonl` llegaba como nombre de archivo: «no existen». Un archivo que existe
    con ese nombre exacto manda, y un comodin que no encuentra nada queda como
    vino, para que el error lo nombre.
    """
    if Path(argumento).is_file() or not any(c in argumento for c in "*?["):
        return [argumento]
    return sorted(glob.glob(argumento)) or [argumento]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

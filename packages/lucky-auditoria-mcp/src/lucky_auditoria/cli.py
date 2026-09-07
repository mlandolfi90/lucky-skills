"""`lucky-auditoria <lectura> <archivos...>` — los lectores desde la terminal.

Sale JSON porque el que lee un registro suele estar encadenando otra cosa, y una
tabla linda obliga a re-parsearla.
"""

import argparse
import json
import sys
from pathlib import Path

from lucky_auditoria import lectores

_LECTURAS = {
    "cazar": lectores.cazar,
    "rechazos": lectores.rechazos,
    "por-sesion": lectores.por_sesion,
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
        help="uno o mas .jsonl; los comodines los expande el shell",
    )
    args = parser.parse_args(argv)

    rutas = [Path(a) for a in args.archivos]
    faltan = [str(r) for r in rutas if not r.is_file()]
    if faltan:
        # Decirlo en vez de devolver una lista vacia: un resultado vacio por
        # archivo inexistente se lee como "no hay nada que reportar".
        print(f"no existen: {', '.join(faltan)}", file=sys.stderr)
        return 2

    salida = _LECTURAS[args.lectura](lectores.leer(rutas))
    print(json.dumps(salida, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

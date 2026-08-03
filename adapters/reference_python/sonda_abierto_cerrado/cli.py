"""CLI de la sonda abierto/cerrado. Asesora: exit 0 salvo --strict."""

from __future__ import annotations

import argparse
from pathlib import Path

from .scanner import escanear


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="raíz del repo git a sondear")
    parser.add_argument("--rev", default="HEAD", help="revisión a analizar (default HEAD)")
    parser.add_argument("--min-ediciones", type=int, default=2)
    parser.add_argument("--max-lineas", type=int, default=40)
    parser.add_argument("--ratio-min", type=float, default=0.75)
    parser.add_argument(
        "--ultimos",
        type=int,
        default=None,
        help="ventana: analizar solo los últimos N commits (modo hook, 'al momento')",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 si hay candidatos (para CI); por defecto la sonda solo avisa",
    )
    args = parser.parse_args(argv)

    candidatos = escanear(
        Path(args.repo),
        rev=args.rev,
        min_ediciones=args.min_ediciones,
        max_lineas_por_edicion=args.max_lineas,
        ratio_min=args.ratio_min,
        ultimos=args.ultimos,
    )
    print("SONDA=ABIERTO_CERRADO")
    print(f"REV={args.rev}")
    print(f"VENTANA={args.ultimos or 'HISTORIA_COMPLETA'}")
    print(f"CANDIDATOS={len(candidatos)}")
    for c in candidatos:
        pista = "SI" if c.pista_nombre else "NO"
        print(
            f"CANDIDATO={c.ruta}|ediciones_aditivas={c.ediciones_aditivas}"
            f"|ediciones_totales={c.ediciones_totales}|pista_nombre={pista}"
        )
    print("MODE=ADVISORY")
    if candidatos:
        print(
            "PRUEBA_DE_FUEGO=una entrada nueva debe poder entrar tocando SOLO su "
            "propio archivo (carpeta detras de un puerto); si esta lista crece "
            "editandose, el punto de extension esta cerrado (saber CAP-2c80bf0aae72)"
        )
    return 1 if (args.strict and candidatos) else 0


if __name__ == "__main__":
    raise SystemExit(main())

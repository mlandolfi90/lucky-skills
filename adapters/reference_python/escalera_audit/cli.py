"""CLI del auditor de escalera. Asesor: exit 0 salvo --strict."""

from __future__ import annotations

import argparse
from pathlib import Path

from .auditor import auditar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="raíz del repo adoptado a auditar")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 si el veredicto es ESCALERA_MUDA (para CI); por defecto solo avisa",
    )
    args = parser.parse_args(argv)

    resultado = auditar(Path(args.target))
    print("AUDIT=ESCALERA")
    print(f"TARGET={args.target}")
    print(f"COMMITS_TOTAL={resultado.commits_total}")
    print(
        "COMMITS_DESDE_ADOPCION="
        + (
            str(resultado.commits_desde_adopcion)
            if resultado.commits_desde_adopcion is not None
            else "N/D"
        )
    )
    print(f"ADOPTADO_DESDE={resultado.adoptado_desde}")
    print(f"CAMBIOS={len(resultado.cambios)}")
    print(f"SOLO_OBSERVACION={resultado.solo_observacion}")
    print(f"CON_DIAGNOSTICO={resultado.con_diagnostico}")
    print(f"CON_CIERRE={resultado.con_cierre}")
    print(f"VEREDICTO={resultado.veredicto}")
    print("MODE=ADVISORY")
    if resultado.veredicto == "ESCALERA_MUDA":
        print(
            "AVISO=el repo commitea sin cerrar: la gobernanza esta instalada y "
            "muda — adoptado no es ejercido"
        )
    return 1 if (args.strict and resultado.veredicto == "ESCALERA_MUDA") else 0


if __name__ == "__main__":
    raise SystemExit(main())

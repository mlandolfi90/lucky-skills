from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from lifecycle_core.envfile import canonical_env
from lifecycle_core.receipts import (
    local_state_root,
    operation_id,
    utc_now,
    write_receipt,
)
from sextante.authority import is_actor

from .scanner import scan_collisions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mapa de colisiones de solo lectura")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--contract", action="append", default=[])
    parser.add_argument("--criterion", action="append", default=[])
    parser.add_argument("--base-fingerprint", default="")
    parser.add_argument("--receipt-root", default="")
    parser.add_argument("--collected-by", default="session:mother")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if not is_actor(arguments.collected_by):
            raise ValueError("--collected-by debe identificar un actor conocido")
        report = scan_collisions(
            workspace=Path(arguments.workspace),
            paths=tuple(arguments.path),
            symbols=tuple(arguments.symbol),
            contracts=tuple(arguments.contract),
            criteria=tuple(arguments.criterion),
            base_fingerprint=arguments.base_fingerprint,
        )
        receipt_root = (
            Path(arguments.receipt_root)
            if arguments.receipt_root
            else local_state_root("collision-map")
        )
        receipt_root.mkdir(parents=True, exist_ok=True)
        receipt_id = operation_id(
            "collision",
            f"{Path(arguments.workspace).resolve()}:{arguments.path}",
        )
        # El alcance consultado viaja en el recibo: sin él, un `NONE` no
        # distingue "consulté esto y no había nada" de "no consulté nada".
        # `QUERY_HASH` es la clave de deduplicación independiente del reloj:
        # misma consulta sobre el mismo workspace, mismo hash.
        query = {
            "QUERY_PATHS": ",".join(sorted(arguments.path)) or "NONE",
            "QUERY_SYMBOLS": ",".join(sorted(arguments.symbol)) or "NONE",
            "QUERY_CONTRACTS": ",".join(sorted(arguments.contract)) or "NONE",
            "QUERY_CRITERIA": ",".join(sorted(arguments.criterion)) or "NONE",
            "QUERY_BASE_FINGERPRINT": arguments.base_fingerprint or "NONE",
        }
        query_hash = hashlib.sha256(
            canonical_env(
                {"WORKSPACE": str(Path(arguments.workspace).resolve()), **query}
            ).encode("utf-8")
        ).hexdigest()
        receipt = write_receipt(
            receipt_root / f"{receipt_id}.env",
            {
                "FORMAT_VERSION": "1",
                "COLLISION_ID": receipt_id,
                "WORKSPACE": str(Path(arguments.workspace).resolve()),
                **query,
                "QUERY_HASH": query_hash,
                "COLLISION": report.state,
                "PATHS": ",".join(report.paths) or "NONE",
                "SYMBOLS": ",".join(report.symbols) or "NONE",
                "CONTRACTS": ",".join(report.contracts) or "NONE",
                "CRITERIA": ",".join(report.criteria) or "NONE",
                "OTHER_ACTORS": ",".join(report.actors) or "NONE",
                "BASE_MISMATCH": report.base_mismatch,
                "RECOMMENDATION": report.recommendation,
                "EVIDENCE": json.dumps(
                    [
                        {
                            "kind": item.kind,
                            "subject": item.subject,
                            "actor": item.actor,
                            "source": item.source,
                        }
                        for item in report.collisions
                    ],
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "COLLECTED_BY": arguments.collected_by,
                "OBSERVED_AT": utc_now(),
            },
        )
        print(f"COLLISION={report.state}")
        print(f"PATHS={','.join(report.paths) or 'NONE'}")
        print(f"SYMBOLS={','.join(report.symbols) or 'NONE'}")
        print(f"CONTRACTS={','.join(report.contracts) or 'NONE'}")
        print(f"CRITERIA={','.join(report.criteria) or 'NONE'}")
        print(f"OTHER_ACTORS={','.join(report.actors) or 'NONE'}")
        print(f"BASE_MISMATCH={report.base_mismatch}")
        print(f"RECOMMENDATION={report.recommendation}")
        print(f"ASSOCIATIONS={len(report.collisions)}")
        if report.base_mismatch == "YES":
            # Bloqueo + advertencia + proposición corta: quién planificó sobre
            # otra base, dónde está declarado, y qué hacer para destrabar.
            print("WARNING=trabajo paralelo planificado sobre una base distinta")
            for item in report.collisions:
                if item.kind == "BASE_MISMATCH":
                    print(f"CONFLICT={item.actor}|base:{item.subject[:12]}|{item.source}")
            print(
                "PROPOSAL=replanificar sobre la base actual y revalidar el "
                "alcance con los actores listados antes de escribir"
            )
        print(f"RECEIPT={receipt.resolve()}")
        return 0
    except (OSError, ValueError) as error:
        print(f"COLLISION_ERROR={error}", file=sys.stderr)
        return 1

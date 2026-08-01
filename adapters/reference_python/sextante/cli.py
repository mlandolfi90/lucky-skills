from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .arguments import build_parser
from .identity import resolve_source_identity
from .receipt_contract import utc_now
from .runner import run_check


VISIBLE_KEYS = (
    "LOCAL",
    "REMOTE",
    "RUNTIME",
    "CAPABILITIES",
    "STATE_VERDICT",
    "READ_GATE",
    "WRITE_GATE",
    "TARGET",
    "RECEIPT",
)


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdout()
    arguments = build_parser().parse_args(argv)
    workspace = Path(arguments.workspace).resolve()
    adapter_root = Path(__file__).resolve().parents[1]
    try:
        identity = resolve_source_identity(
            explicit_version=arguments.skill_version,
            explicit_source_root=arguments.source_root,
            adapter_root=adapter_root,
        )
        result = run_check(
            arguments=arguments,
            workspace=workspace,
            started_at=utc_now(),
            skill_version=identity.skill_version,
            skill_version_source=identity.version_source,
            source_root=identity.source_root,
            adapter_root=adapter_root,
        )
    except (OSError, ValueError) as error:
        print(f"SEXTANTE_ERROR={error}")
        return 2

    for key in VISIBLE_KEYS:
        print(f"{key}={result[key]}")
    if result["HUMAN_DECISION"] != "NONE":
        print(f"HUMAN_DECISION={result['HUMAN_DECISION']}")
        print(f"DECISION_REASON={result['DECISION_REASON']}")
    return 0


def _parser() -> argparse.ArgumentParser:
    """Compatibility seam used by conformance tests and future adapters."""
    return build_parser()


def _configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="strict")
    except (OSError, ValueError):
        return

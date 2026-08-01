"""CLI para el contrato JSON portable."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .contracts import HookEvent
from .dispatcher import dispatch_event


MAX_EVENT_BYTES = 16 * 1024
DISABLED_VALUES = frozenset({"0", "false", "no", "off", "disabled"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatcher portable de hooks asesores"
    )
    parser.add_argument("--receipt-root", required=True)
    parser.add_argument("--disabled", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        event = HookEvent.from_mapping(_read_json_stdin())
        result = dispatch_event(
            event,
            receipt_root=Path(arguments.receipt_root),
            enabled=not arguments.disabled and _enabled_by_environment(),
        )
        print(
            json.dumps(
                result.to_mapping(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError) as error:
        print(f"HOOK_ERROR={error}", file=sys.stderr)
        return 1


def _read_json_stdin() -> dict[str, object]:
    raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
    if len(raw) > MAX_EVENT_BYTES:
        raise ValueError("evento JSON demasiado grande")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("evento JSON inválido") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("evento debe ser un objeto JSON")
    return value


def _enabled_by_environment() -> bool:
    value = os.environ.get("LIFECYCLE_HOOKS_ENABLED", "1")
    return value.strip().lower() not in DISABLED_VALUES

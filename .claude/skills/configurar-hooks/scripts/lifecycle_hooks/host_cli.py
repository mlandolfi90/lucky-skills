from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .dispatcher import dispatch_event
from .normalizer import host_error_response, host_response, normalize_host_event


MAX_HOST_EVENT_BYTES = 64 * 1024
DISABLED_VALUES = frozenset({"0", "false", "no", "off", "disabled"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adaptador de hook por harness")
    parser.add_argument("--harness", required=True, choices=("claude-code", "codex"))
    parser.add_argument("--event", required=True)
    parser.add_argument("--workspace", default="")
    parser.add_argument("--receipt-root", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        payload = _read_host_payload()
        workspace = _workspace(arguments.workspace, payload)
        receipt_root = (
            Path(arguments.receipt_root)
            if arguments.receipt_root
            else workspace / ".lifecycle" / "local" / "hooks"
        )
        event = normalize_host_event(
            harness=arguments.harness,
            declared_event=arguments.event,
            payload=payload,
            workspace=workspace,
        )
        result = (
            dispatch_event(
                event,
                receipt_root=receipt_root,
                enabled=_enabled_by_environment(),
            )
            if event is not None
            else None
        )
        _print_response(
            host_response(
                result,
                harness=arguments.harness,
                declared_event=arguments.event,
            )
        )
    except (OSError, ValueError):
        _print_response(host_error_response(arguments.harness))
    return 0


def _read_host_payload() -> dict[str, object]:
    raw = sys.stdin.buffer.read(MAX_HOST_EVENT_BYTES + 1)
    if len(raw) > MAX_HOST_EVENT_BYTES:
        raise ValueError("payload de harness demasiado grande")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("payload de harness inválido") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("payload de harness debe ser un objeto")
    return value


def _enabled_by_environment() -> bool:
    value = os.environ.get("LIFECYCLE_HOOKS_ENABLED", "1")
    return value.strip().lower() not in DISABLED_VALUES


def _workspace(requested: str, payload: dict[str, object]) -> Path:
    if requested:
        return Path(requested).resolve()
    raw_cwd = payload.get("cwd", ".")
    cwd = Path(raw_cwd if isinstance(raw_cwd, str) and raw_cwd else ".").resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _print_response(response: dict[str, object]) -> None:
    print(
        json.dumps(
            response,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )

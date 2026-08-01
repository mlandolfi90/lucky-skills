from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .envfile import canonical_env, load_env, write_immutable_atomic


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def operation_id(prefix: str, seed: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{timestamp}-{suffix}"


def content_hash(values: Mapping[str, object]) -> str:
    filtered = {key: value for key, value in values.items() if key != "RECEIPT_HASH"}
    return hashlib.sha256(canonical_env(filtered).encode("utf-8")).hexdigest()


def write_receipt(path: Path, values: Mapping[str, object]) -> Path:
    payload = dict(values)
    payload["RECEIPT_HASH"] = content_hash(payload)
    write_immutable_atomic(path, canonical_env(payload))
    return path


def verify_receipt(path: Path) -> bool:
    try:
        values = load_env(path)
    except (OSError, ValueError):
        return False
    expected = values.get("RECEIPT_HASH", "")
    return bool(expected) and expected == content_hash(values)


def local_state_root(namespace: str) -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "skills-v3" / namespace

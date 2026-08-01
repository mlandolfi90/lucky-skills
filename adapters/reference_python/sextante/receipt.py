from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Mapping

from .envfile import canonical_env, read_stable_utf8, write_immutable_atomic
from .receipt_validator import validate_receipt_document


MAX_LIFECYCLE_GITIGNORE_BYTES = 64 * 1024


def write_receipt(
    values: Mapping[str, object],
    *,
    workspace: Path,
    receipt_root: Path | None,
) -> tuple[Path, str]:
    payload = canonical_env(values)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    full_values = dict(values)
    full_values["RECEIPT_HASH"] = digest
    content = canonical_env(full_values)
    validation_errors = validate_receipt_document(content)
    if validation_errors:
        raise ValueError("comprobante no conforme: " + ",".join(validation_errors))

    target_directory = receipt_directory(workspace=workspace, receipt_root=receipt_root)
    target_path = target_directory / f"{values['RECEIPT_ID']}.env"
    write_immutable_atomic(target_path, content)
    return target_path, digest


def receipt_directory(*, workspace: Path, receipt_root: Path | None) -> Path:
    if receipt_root is not None:
        resolved_root = receipt_root.resolve()
        if _is_within(resolved_root, workspace.resolve()):
            raise ValueError("receipt_root debe quedar fuera del workspace")
        workspace_id = hashlib.sha256(
            str(workspace.resolve()).encode("utf-8")
        ).hexdigest()[:16]
        return resolved_root / workspace_id

    lifecycle = workspace / ".lifecycle"
    local_root = lifecycle / "local"
    ignore_file = lifecycle / ".gitignore"
    if (
        lifecycle.is_dir()
        and not _is_linklike(lifecycle)
        and not (local_root.exists() and _is_linklike(local_root))
        and _local_state_is_ignored(ignore_file)
    ):
        candidate = local_root / "sextante"
        if not (candidate.exists() and _is_linklike(candidate)) and _is_within(
            candidate.resolve(), workspace.resolve()
        ):
            return candidate

    base = _external_state_root(workspace)
    workspace_id = hashlib.sha256(str(workspace.resolve()).encode("utf-8")).hexdigest()[
        :16
    ]
    return base / "sextante" / "receipts" / workspace_id


def _local_state_is_ignored(ignore_file: Path) -> bool:
    try:
        content = read_stable_utf8(
            ignore_file,
            max_bytes=MAX_LIFECYCLE_GITIGNORE_BYTES,
        )
    except (OSError, ValueError):
        return False
    active_lines = tuple(
        line for line in content.splitlines() if line and not line.startswith("#")
    )
    return bool(active_lines) and active_lines[-1] == "local/"


def _external_state_root(workspace: Path) -> Path:
    configured = (
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("XDG_STATE_HOME"),
        tempfile.gettempdir(),
    )
    resolved_workspace = workspace.resolve()
    for value in configured:
        if not value:
            continue
        try:
            candidate = Path(value).expanduser().resolve()
        except OSError:
            continue
        if candidate.exists() and not candidate.is_dir():
            continue
        if not _is_within(candidate, resolved_workspace):
            return candidate
    raise ValueError("no existe almacenamiento local del harness fuera del workspace")


def verify_receipt(path: Path) -> bool:
    from .receipt_validator import is_valid_receipt

    return is_valid_receipt(path)


def display_path(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()

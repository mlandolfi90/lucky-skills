from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from lifecycle_core.authorization import require_human
from lifecycle_core.envfile import load_env
from lifecycle_core.locking import directory_lock
from lifecycle_core.receipts import operation_id, utc_now, verify_receipt, write_receipt
from sextante.authority import is_actor


KINDS = {
    "OBSERVATION",
    "DIAGNOSIS",
    "MICROFIX",
    "HOTFIX",
    "FEATURE",
    "QUALITY",
    "REFACTOR",
    "MIGRATION",
    "CLOSURE",
    "AUTOPSY",
}
WRITING_KINDS = {
    "MICROFIX",
    "HOTFIX",
    "FEATURE",
    "QUALITY",
    "REFACTOR",
    "MIGRATION",
}
TRANSITIONS = {
    "OBSERVATION": {"DIAGNOSIS", "CLOSURE"},
    "DIAGNOSIS": {
        "MICROFIX",
        "HOTFIX",
        "FEATURE",
        "QUALITY",
        "REFACTOR",
        "MIGRATION",
        "CLOSURE",
    },
    "MICROFIX": {"MICROFIX", "QUALITY", "REFACTOR", "CLOSURE", "AUTOPSY"},
    "HOTFIX": {"QUALITY", "REFACTOR", "CLOSURE", "AUTOPSY"},
    "FEATURE": {"CLOSURE", "AUTOPSY"},
    "QUALITY": {"CLOSURE", "AUTOPSY"},
    "REFACTOR": {"CLOSURE", "AUTOPSY"},
    "MIGRATION": {"CLOSURE", "AUTOPSY"},
    "CLOSURE": {"AUTOPSY"},
    "AUTOPSY": set(),
}
CHANGE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{7,95}$")


def create_observation(
    *,
    workspace: Path,
    summary: str,
    scope: str,
    author: str,
    confirmed_by: str,
    observed: str = "",
    expected: str = "",
) -> Path:
    _validate_actor(author)
    require_human(confirmed_by, field="confirmed_by")
    normalized_scope = scope.upper()
    if normalized_scope not in {"GLOBAL", "LOCAL"}:
        raise ValueError("scope debe ser GLOBAL o LOCAL")
    change_id = operation_id("change", summary).lower()
    return _append(
        workspace=workspace,
        change_id=change_id,
        kind="OBSERVATION",
        author=author,
        confirmed_by=confirmed_by,
        fields={
            "SUMMARY": _required(summary, "summary"),
            "SCOPE": normalized_scope,
            "OBSERVED": observed or "UNKNOWN",
            "EXPECTED": expected or "UNKNOWN",
            "TARGET_WHERE": "UNCONFIRMED",
        },
        previous=None,
    )


def append_record(
    *,
    workspace: Path,
    change_id: str,
    kind: str,
    author: str,
    confirmed_by: str,
    summary: str,
    target_where: str = "UNCONFIRMED",
    evidence: str = "",
    rollback: str = "",
) -> Path:
    normalized_kind = kind.upper()
    if normalized_kind not in KINDS - {"OBSERVATION", "CLOSURE", "AUTOPSY"}:
        raise ValueError("kind no permitido por record")
    normalized_target = (
        _confirmed_target(target_where)
        if normalized_kind in WRITING_KINDS
        else _optional_target(target_where)
    )
    return _append(
        workspace=workspace,
        change_id=_validate_change_id(change_id),
        kind=normalized_kind,
        author=author,
        confirmed_by=confirmed_by,
        fields={
            "SUMMARY": _required(summary, "summary"),
            "TARGET_WHERE": normalized_target,
            "EVIDENCE": evidence or "UNKNOWN",
            "ROLLBACK": rollback or "UNKNOWN",
        },
    )


def close_change(
    *,
    workspace: Path,
    change_id: str,
    status: str,
    result: str,
    author: str,
    confirmed_by: str,
    tests: str,
    architecture: str,
    collision: str,
    conditions: str = "",
) -> Path:
    normalized_status = status.upper()
    if normalized_status not in {"FINAL", "CONDITIONAL", "BLOCKED"}:
        raise ValueError("closure debe ser FINAL, CONDITIONAL o BLOCKED")
    normalized_conditions = (
        _required(conditions, "conditions") if conditions.strip() else ""
    )
    if normalized_status == "CONDITIONAL" and not normalized_conditions:
        raise ValueError("un cierre CONDITIONAL exige conditions")
    has_writing_phase = _has_writing_phase(workspace, change_id)
    accepted_tests = {"PASS"} if has_writing_phase else {"PASS", "NOT_APPLICABLE"}
    if normalized_status == "FINAL" and (
        tests not in accepted_tests
        or architecture not in {"PASS", "NOT_APPLICABLE"}
        or collision != "NONE"
    ):
        raise ValueError("un cierre FINAL no cumple sus gates")
    return _append(
        workspace=workspace,
        change_id=_validate_change_id(change_id),
        kind="CLOSURE",
        author=author,
        confirmed_by=confirmed_by,
        fields={
            "CLOSURE": normalized_status,
            "RESULT": _required(result, "result"),
            "TESTS": tests,
            "ARCHITECTURE": architecture,
            "COLLISION": collision,
            "CONDITIONS": normalized_conditions or "NONE",
        },
    )


def record_autopsy(
    *,
    workspace: Path,
    change_id: str,
    author: str,
    confirmed_by: str,
    root_cause: str,
    correction: str,
    recovery_evidence: str,
    prevention: str,
) -> Path:
    return _append(
        workspace=workspace,
        change_id=_validate_change_id(change_id),
        kind="AUTOPSY",
        author=author,
        confirmed_by=confirmed_by,
        fields={
            "ROOT_CAUSE": _required(root_cause, "root_cause"),
            "CORRECTION": _required(correction, "correction"),
            "RECOVERY_EVIDENCE": _required(
                recovery_evidence,
                "recovery_evidence",
            ),
            "PREVENTION": _required(prevention, "prevention"),
        },
    )


def records(workspace: Path, change_id: str) -> tuple[Path, ...]:
    root = _change_root(workspace, _validate_change_id(change_id))
    return tuple(sorted(root.glob("[0-9][0-9][0-9]-*.env"))) if root.exists() else ()


def _append(
    *,
    workspace: Path,
    change_id: str,
    kind: str,
    author: str,
    confirmed_by: str,
    fields: Mapping[str, object],
    previous: Path | None = None,
) -> Path:
    root = workspace.resolve(strict=True)
    if not (root / ".lifecycle").is_dir():
        raise ValueError("el proyecto aún no fue adoptado")
    _validate_actor(author)
    require_human(confirmed_by, field="confirmed_by")
    change_root = _change_root(root, change_id)
    lock_path = root / ".lifecycle" / "local" / "locks" / f"change-{change_id}"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with directory_lock(
        lock_path,
        {
            "CHANGE_ID": change_id,
            "KIND": kind,
            "OWNER": author,
            "CREATED_AT": utc_now(),
        },
    ):
        existing = records(root, change_id)
        prior = previous or (existing[-1] if existing else None)
        if kind == "OBSERVATION" and prior is not None:
            raise ValueError("OBSERVATION debe iniciar el cambio")
        if kind != "OBSERVATION":
            if prior is None or not verify_receipt(prior):
                raise ValueError("la fase anterior falta o es inválida")
            prior_values = load_env(prior)
            prior_kind = prior_values.get("KIND", "")
            if kind not in TRANSITIONS.get(prior_kind, set()):
                raise ValueError(f"transición inválida: {prior_kind}->{kind}")
        sequence = len(existing) + 1
        values: dict[str, object] = {
            "FORMAT_VERSION": "1",
            "CHANGE_ID": change_id,
            "SEQUENCE": str(sequence),
            "KIND": kind,
            "PREVIOUS_RECORD": str(prior) if prior else "NONE",
            "AUTHOR": author,
            "CONFIRMED_BY": confirmed_by,
            "CREATED_AT": utc_now(),
        }
        values.update(fields)
        change_root.mkdir(parents=True, exist_ok=True)
        return write_receipt(
            change_root / f"{sequence:03d}-{kind.lower()}.env",
            values,
        )


def _change_root(workspace: Path, change_id: str) -> Path:
    return workspace / ".lifecycle" / "changes" / change_id


def _validate_change_id(value: str) -> str:
    if not CHANGE_ID_PATTERN.fullmatch(value):
        raise ValueError("CHANGE_ID inválido")
    return value


def _validate_actor(actor: str) -> None:
    if not is_actor(actor):
        raise ValueError("author debe ser un actor conocido")


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} es obligatorio")
    if any(character in normalized for character in "\r\n\0"):
        raise ValueError(f"{field} debe ocupar una sola línea")
    return normalized


def _confirmed_target(value: str) -> str:
    normalized = _required(value, "TARGET")
    if normalized.upper() in {"UNCONFIRMED", "UNKNOWN", "N/D", "NONE"}:
        raise ValueError("un cambio escritor exige TARGET confirmado")
    return normalized


def _optional_target(value: str) -> str:
    normalized = value.strip() or "UNCONFIRMED"
    if any(character in normalized for character in "\r\n\0"):
        raise ValueError("TARGET debe ocupar una sola línea")
    return normalized


def _has_writing_phase(workspace: Path, change_id: str) -> bool:
    return any(
        load_env(path).get("KIND", "") in WRITING_KINDS
        for path in records(workspace, _validate_change_id(change_id))
    )

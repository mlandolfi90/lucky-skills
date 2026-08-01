from __future__ import annotations

import hashlib
from pathlib import Path

from .envfile import canonical_env, load_env_document, parse_env
from .receipt_schema import HEX_64, validate_schema
from .receipt_semantics import validate_semantics


FORBIDDEN_KEY_PARTS = {
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "CREDENTIAL",
    "PRIVATE_KEY",
}


def validate_receipt(path: Path) -> tuple[str, ...]:
    try:
        raw, values = load_env_document(path)
    except (OSError, UnicodeError, ValueError) as error:
        return (str(error),)

    return _validate_loaded(raw, values)


def validate_receipt_document(raw: str) -> tuple[str, ...]:
    try:
        values = parse_env(raw, source="<receipt>")
    except ValueError as error:
        return (str(error),)
    return _validate_loaded(raw, values)


def _validate_loaded(raw: str, values: dict[str, str]) -> tuple[str, ...]:
    errors = validate_schema(values)
    if canonical_env(values) != raw:
        errors.append("NON_CANONICAL_ENV")
    if not values or next(reversed(values), "") != "RECEIPT_HASH":
        errors.append("RECEIPT_HASH_NOT_LAST")
    _validate_hash(values, errors)
    errors.extend(validate_semantics(values))
    for key in values:
        if any(part in key for part in FORBIDDEN_KEY_PARTS):
            errors.append(f"FORBIDDEN_SENSITIVE_KEY:{key}")
    return tuple(dict.fromkeys(errors))


def is_valid_receipt(path: Path) -> bool:
    return not validate_receipt(path)


def _validate_hash(values: dict[str, str], errors: list[str]) -> None:
    recorded_hash = values.get("RECEIPT_HASH", "")
    if not HEX_64.fullmatch(recorded_hash):
        errors.append("INVALID_RECEIPT_HASH")
        return
    unhashed = dict(values)
    unhashed.pop("RECEIPT_HASH", None)
    expected_hash = hashlib.sha256(canonical_env(unhashed).encode("utf-8")).hexdigest()
    if recorded_hash != expected_hash:
        errors.append("RECEIPT_HASH_MISMATCH")

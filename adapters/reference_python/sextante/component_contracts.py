from __future__ import annotations

import re

from .authority import is_human_actor
from .git_ref import valid_remote_ref

STATE_MAP_FIELDS = {
    "STATE_SCHEMA",
    "STATE_REVISION",
    "GIT_LOCAL_COMMIT",
    "GIT_LOCAL_FINGERPRINT",
    "GIT_REMOTE_COMMIT",
    "GIT_REMOTE_REF",
    "RUNTIME_VERSION",
    "CAPABILITIES_HASH",
    "TARGET_WHERE",
    "TARGET_ACTION",
    "TARGET_CONFIRMED_BY",
}
UNKNOWN_VALUES = frozenset({"UNKNOWN", "N/D", "NOT_APPLICABLE"})
COMMIT_SPECIAL_VALUES = UNKNOWN_VALUES | {"NO_COMMIT"}
REMOTE_NAME_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._/-]{0,127}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REVISION_PATTERN = re.compile(r"^[0-9]+$")
POLICY_LIMITS = {
    "REMOTE_MAX_AGE_SECONDS": 86_400,
    "RUNTIME_MAX_AGE_SECONDS": 86_400,
    "CAPABILITIES_MAX_AGE_SECONDS": 86_400,
    "COLLECTOR_TIMEOUT_SECONDS": 60,
    "WORKSPACE_MAX_ENTRIES": 50_000,
}
POLICY_DEFAULTS = {
    "REMOTE_MAX_AGE_SECONDS": 900,
    "RUNTIME_MAX_AGE_SECONDS": 600,
    "CAPABILITIES_MAX_AGE_SECONDS": 300,
    "COLLECTOR_TIMEOUT_SECONDS": 10,
    "WORKSPACE_MAX_ENTRIES": 2_000,
}


def valid_policy(values: dict[str, str]) -> bool:
    readme_policy = values.get("README_POLICY")
    if readme_policy is not None and readme_policy.upper() != "IGNORE":
        return False
    return all(
        key not in values or _positive_int(values[key], maximum)
        for key, maximum in POLICY_LIMITS.items()
    )


def valid_sources(values: dict[str, str]) -> bool:
    remote_name = values.get("REMOTE_NAME", "AUTO")
    if remote_name != "AUTO" and not REMOTE_NAME_PATTERN.fullmatch(remote_name):
        return False
    if values.get("RUNTIME_MODE", "UNDECLARED").upper() not in {
        "UNDECLARED",
        "NONE",
    }:
        return False
    candidates = [
        candidate.strip()
        for candidate in values.get("RUNTIME_CANDIDATES", "").split(",")
        if candidate.strip()
    ]
    return len(candidates) <= 32 and all(_safe_text(item) for item in candidates)


def valid_state_map(values: dict[str, str]) -> bool:
    if not STATE_MAP_FIELDS.issubset(values):
        return False
    if values["STATE_SCHEMA"] != "1":
        return False
    if not REVISION_PATTERN.fullmatch(values["STATE_REVISION"]):
        return False
    for field in ("GIT_LOCAL_COMMIT", "GIT_REMOTE_COMMIT"):
        if not _known_or_pattern(
            values[field], COMMIT_PATTERN, special_values=COMMIT_SPECIAL_VALUES
        ):
            return False
    if not valid_remote_ref(values["GIT_REMOTE_REF"]):
        return False
    if (
        values["GIT_REMOTE_COMMIT"].upper() not in COMMIT_SPECIAL_VALUES
        and values["GIT_REMOTE_REF"] in UNKNOWN_VALUES
    ):
        return False
    for field in ("GIT_LOCAL_FINGERPRINT", "CAPABILITIES_HASH"):
        if not _known_or_pattern(values[field], HASH_PATTERN):
            return False
    if not _safe_text(values["RUNTIME_VERSION"]):
        return False
    target = (
        values["TARGET_WHERE"],
        values["TARGET_ACTION"],
        values["TARGET_CONFIRMED_BY"],
    )
    if target == ("UNCONFIRMED", "UNCONFIRMED", "UNCONFIRMED"):
        return True
    return (
        all(_safe_text(item) for item in target)
        and values["TARGET_ACTION"] in {"EDIT", "PUSH", "DEPLOY"}
        and is_human_actor(values["TARGET_CONFIRMED_BY"])
    )


def _known_or_pattern(
    value: str,
    pattern: re.Pattern[str],
    *,
    special_values: frozenset[str] = UNKNOWN_VALUES,
) -> bool:
    return value.upper() in special_values or bool(pattern.fullmatch(value))


def _positive_int(value: str, maximum: int) -> bool:
    try:
        parsed = int(value)
    except ValueError:
        return False
    return 0 < parsed <= maximum


def _safe_text(value: str) -> bool:
    return (
        bool(value)
        and len(value) <= 256
        and not any(character in value for character in "\r\n\0")
    )

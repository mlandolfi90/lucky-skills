from __future__ import annotations

import re
from datetime import datetime

from .arguments import EVIDENCE_LEVELS, SOURCE_RESULTS
from .git_ref import valid_remote_ref
from .observations import MAX_CAPABILITY_COUNT


REQUIRED_FIELDS = {
    "RECEIPT_SCHEMA",
    "RECEIPT_ID",
    "RECEIPT_HASH",
    "SKILL_VERSION",
    "SKILL_VERSION_SOURCE",
    "SKILL_VERSION_FINISHED",
    "CONTRACT_VERSION",
    "ADAPTER_ID",
    "ADAPTER_VERSION",
    "HARNESS",
    "EXECUTION_LEVEL",
    "INTENT",
    "STARTED_AT_UTC",
    "FINISHED_AT_UTC",
    "WORKSPACE_ID",
    "WORKSPACE_PATH",
    "LIFECYCLE",
    "CONFIG_STATUS",
    "POLICY_STATUS",
    "SOURCES_STATUS",
    "STATE_MAP_STATUS",
    "README_POLICY",
    "README_POLICY_SOURCE",
    "README_POLICY_CONFIRMED_BY",
    "LOCAL",
    "LOCAL_VERSIONING",
    "LOCAL_SOURCE",
    "LOCAL_EVIDENCE_LEVEL",
    "LOCAL_FINGERPRINT_MODE",
    "LOCAL_FINGERPRINT",
    "LOCAL_FINGERPRINT_STARTED",
    "LOCAL_FINGERPRINT_FINISHED",
    "LOCAL_CHANGED_DURING_CHECK",
    "LOCAL_COMMIT",
    "LOCAL_BRANCH",
    "LOCAL_DIRTY",
    "LOCAL_DIRTY_MODE",
    "LOCAL_DIRTY_COUNT",
    "LOCAL_ENTRY_COUNT",
    "LOCAL_SCAN_STATUS",
    "LOCAL_GIT_SAFE_OVERRIDE",
    "LOCAL_OBSERVED_AT_UTC",
    "ADAPTER_FINGERPRINT_STARTED",
    "ADAPTER_FINGERPRINT_FINISHED",
    "ADAPTER_FINAL_STATUS",
    "ADAPTER_CHANGED_DURING_CHECK",
    "OBSERVATION_BOUNDARY",
    "REMOTE",
    "REMOTE_STATE",
    "REMOTE_NAME",
    "REMOTE_URL",
    "REMOTE_COMMIT",
    "REMOTE_REF",
    "REMOTE_SOURCE_ID",
    "REMOTE_QUERY_CONFIRMED_SOURCE_ID",
    "REMOTE_REDIRECT_POLICY",
    "REMOTE_QUERY_ATTEMPTED",
    "REMOTE_CANDIDATES",
    "REMOTE_EVIDENCE_LEVEL",
    "REMOTE_QUERY_CONFIRMED_BY",
    "REMOTE_MAX_AGE_SECONDS",
    "REMOTE_OBSERVED_AT_UTC",
    "RUNTIME",
    "RUNTIME_STATE",
    "RUNTIME_VERSION",
    "RUNTIME_TARGET",
    "RUNTIME_SOURCE",
    "RUNTIME_CANDIDATES",
    "RUNTIME_MAX_AGE_SECONDS",
    "RUNTIME_EVIDENCE_LEVEL",
    "RUNTIME_OBSERVED_AT_UTC",
    "CAPABILITIES",
    "CAPABILITIES_STATE",
    "CAPABILITIES_HASH",
    "CAPABILITIES_SOURCE",
    "CAPABILITY_COUNT",
    "CAPABILITIES_MAX_AGE_SECONDS",
    "CAPABILITIES_EVIDENCE_LEVEL",
    "CAPABILITIES_OBSERVED_AT_UTC",
    "STATE_VERDICT",
    "READ_GATE",
    "WRITE_GATE",
    "TARGET",
    "TARGET_WHERE",
    "TARGET_ACTION",
    "TARGET_CONFIRMED_BY",
    "HUMAN_DECISION",
    "DECISION_REASON",
    "COLLECTED_BY",
    "SYNTHESIZED_BY",
    "DECIDED_BY",
}
HEX_16 = re.compile(r"^[0-9a-f]{16}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
VERSION_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$")
RECEIPT_ID_PATTERN = re.compile(r"^sextante-[0-9A-Za-z._-]{1,128}$")
SOURCE_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
STATE_VERDICTS = {"ALIGNED", "DRIFT", "PARTIAL", "STALE"}
COMPONENT_STATES = {"LOADED", "ABSENT", "INVALID"}
BOOLEAN_VALUES = {"TRUE", "FALSE"}
REMOTE_STATES = {
    "EVIDENCE_EXPIRED",
    "GIT_UNAVAILABLE",
    "LOCAL_BRANCH_UNAVAILABLE",
    "MALFORMED_URL",
    "MULTIPLE_CANDIDATES",
    "MULTIPLE_URLS",
    "NETWORK_CONFIRMATION_REQUIRED",
    "NO_GIT",
    "NO_REMOTE",
    "OUTPUT_LIMIT",
    "REF_NOT_FOUND",
    "REMOTE_RESPONSE_INVALID",
    "SOURCE_CONFIRMATION_MISMATCH",
    "TIMEOUT",
    "UNKNOWN_SELECTION",
    "UNREACHABLE",
    "UNSAFE_URL_COMPONENTS",
    "UNSUPPORTED_SAFE_TRANSPORT",
    "URL_UNAVAILABLE",
    "VERIFIED",
}


def validate_schema(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS.difference(values))
    if missing:
        errors.append(f"MISSING_FIELDS:{','.join(missing)}")

    _expect(values, "RECEIPT_SCHEMA", {"1"}, errors)
    _expect(values, "CONTRACT_VERSION", {"1"}, errors)
    _expect(
        values, "EXECUTION_LEVEL", {"NATIVE", "ADAPTED", "DEGRADED", "MANUAL"}, errors
    )
    _expect(values, "INTENT", {"read", "edit", "push", "deploy"}, errors)
    _expect(
        values, "README_POLICY", {"IGNORE", "DISCOVERY_ONLY", "DECLARED_TRUST"}, errors
    )
    _expect(
        values,
        "README_POLICY_SOURCE",
        {"DEFAULT", "SESSION_OVERRIDE", "SESSION_HUMAN"},
        errors,
    )
    _expect(
        values,
        "LIFECYCLE",
        {"ADOPTED", "NOT_ADOPTED", "INVALID"},
        errors,
    )
    _expect(values, "CONFIG_STATUS", {"VALID", "INVALID"}, errors)
    _expect(
        values,
        "LOCAL_VERSIONING",
        {"GIT", "NO_COMMIT", "UNVERSIONED", "UNKNOWN"},
        errors,
    )
    _expect(
        values,
        "LOCAL_FINGERPRINT_MODE",
        {"INDEX_CONTENT_BOUNDED", "TREE_CONTENT_BOUNDED"},
        errors,
    )
    _expect(values, "LOCAL_DIRTY", BOOLEAN_VALUES, errors)
    _expect(
        values,
        "LOCAL_DIRTY_MODE",
        {"RAW_NO_FILTERS_CONSERVATIVE"},
        errors,
    )
    _expect(values, "LOCAL_GIT_SAFE_OVERRIDE", {"PER_COMMAND", "NOT_REQUIRED"}, errors)
    _expect(values, "REMOTE_STATE", REMOTE_STATES, errors)
    _expect(values, "REMOTE_REDIRECT_POLICY", {"DENY"}, errors)
    _expect(values, "REMOTE_QUERY_ATTEMPTED", BOOLEAN_VALUES, errors)
    _expect(values, "ADAPTER_FINAL_STATUS", {"COMPLETE", "UNAVAILABLE"}, errors)
    _expect(values, "TARGET", {"UNCONFIRMED", "CONFIRMED"}, errors)
    _expect(values, "TARGET_ACTION", {"UNCONFIRMED", "EDIT", "PUSH", "DEPLOY"}, errors)
    _expect(values, "STATE_VERDICT", STATE_VERDICTS, errors)
    _expect(values, "READ_GATE", {"PASS", "WARN"}, errors)
    _expect(values, "WRITE_GATE", {"PASS", "BLOCK"}, errors)
    _expect(
        values,
        "HUMAN_DECISION",
        {
            "NONE",
            "CONFIRM_TARGET",
            "CHOOSE_SOURCE",
            "PROVIDE_ACCESS",
            "CONFIRM_SOURCE_ACCESS",
            "ACCEPT_RISK",
            "STOP",
        },
        errors,
    )
    for field in ("LOCAL", "REMOTE", "RUNTIME", "CAPABILITIES"):
        _expect(values, field, SOURCE_RESULTS, errors)
    for field in ("POLICY_STATUS", "SOURCES_STATUS", "STATE_MAP_STATUS"):
        _expect(values, field, COMPONENT_STATES, errors)
    for field in ("LOCAL_CHANGED_DURING_CHECK", "ADAPTER_CHANGED_DURING_CHECK"):
        _expect(values, field, BOOLEAN_VALUES, errors)
    for field in (
        "LOCAL_EVIDENCE_LEVEL",
        "REMOTE_EVIDENCE_LEVEL",
        "RUNTIME_EVIDENCE_LEVEL",
        "CAPABILITIES_EVIDENCE_LEVEL",
    ):
        _expect(values, field, EVIDENCE_LEVELS, errors)

    _validate_identifiers(values, errors)
    _validate_numbers(values, errors)
    _validate_timestamps(values, errors)
    _validate_cross_fields(values, errors)
    return errors


def parse_utc(value: str) -> datetime | None:
    if not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        return None
    return parsed


def _validate_identifiers(values: dict[str, str], errors: list[str]) -> None:
    if not RECEIPT_ID_PATTERN.fullmatch(values.get("RECEIPT_ID", "")):
        errors.append("INVALID_RECEIPT_ID")
    if not HEX_16.fullmatch(values.get("WORKSPACE_ID", "")):
        errors.append("INVALID_WORKSPACE_ID")
    for field in ("SKILL_VERSION", "ADAPTER_VERSION"):
        if field in values and not VERSION_PATTERN.fullmatch(values[field]):
            errors.append(f"INVALID_VERSION:{field}")
    finished_version = values.get("SKILL_VERSION_FINISHED", "")
    if finished_version != "UNAVAILABLE" and not VERSION_PATTERN.fullmatch(
        finished_version
    ):
        errors.append("INVALID_VERSION:SKILL_VERSION_FINISHED")
    for field in (
        "LOCAL_FINGERPRINT",
        "LOCAL_FINGERPRINT_STARTED",
        "ADAPTER_FINGERPRINT_STARTED",
        "CAPABILITIES_HASH",
    ):
        if field in values and not HEX_64.fullmatch(values[field]):
            errors.append(f"INVALID_FINGERPRINT:{field}")
    for field in ("LOCAL_FINGERPRINT_FINISHED", "ADAPTER_FINGERPRINT_FINISHED"):
        value = values.get(field, "")
        if value != "UNAVAILABLE" and not HEX_64.fullmatch(value):
            errors.append(f"INVALID_FINGERPRINT:{field}")
    source_id = values.get("REMOTE_SOURCE_ID", "")
    if source_id not in {"NOT_APPLICABLE", "UNRESOLVED"} and not (
        SOURCE_ID_PATTERN.fullmatch(source_id)
    ):
        errors.append("INVALID_REMOTE_SOURCE_ID")
    confirmed_source_id = values.get("REMOTE_QUERY_CONFIRMED_SOURCE_ID", "")
    if confirmed_source_id != "UNCONFIRMED" and not (
        SOURCE_ID_PATTERN.fullmatch(confirmed_source_id)
    ):
        errors.append("INVALID_REMOTE_CONFIRMED_SOURCE_ID")
    if not valid_remote_ref(values.get("REMOTE_REF", "")):
        errors.append("INVALID_REMOTE_REF")
    if not _safe_text(values.get("RUNTIME_TARGET", ""), maximum=512):
        errors.append("INVALID_RUNTIME_TARGET")


def _validate_numbers(values: dict[str, str], errors: list[str]) -> None:
    for field in ("LOCAL_DIRTY_COUNT", "LOCAL_ENTRY_COUNT"):
        if not _integer_in_range(values.get(field), minimum=0, maximum=1_000_000):
            errors.append(f"INVALID_INTEGER:{field}")
    if not _integer_in_range(
        values.get("CAPABILITY_COUNT"),
        minimum=0,
        maximum=MAX_CAPABILITY_COUNT,
    ):
        errors.append("INVALID_INTEGER:CAPABILITY_COUNT")
    for field in (
        "REMOTE_MAX_AGE_SECONDS",
        "RUNTIME_MAX_AGE_SECONDS",
        "CAPABILITIES_MAX_AGE_SECONDS",
    ):
        if not _integer_in_range(values.get(field), minimum=1, maximum=86_400):
            errors.append(f"INVALID_INTEGER:{field}")


def _validate_timestamps(values: dict[str, str], errors: list[str]) -> None:
    parsed: dict[str, datetime] = {}
    for field, value in values.items():
        if not field.endswith("_AT_UTC"):
            continue
        timestamp = parse_utc(value)
        if timestamp is None:
            errors.append(f"INVALID_TIMESTAMP:{field}")
        else:
            parsed[field] = timestamp
    started = parsed.get("STARTED_AT_UTC")
    finished = parsed.get("FINISHED_AT_UTC")
    if started and finished and finished < started:
        errors.append("INVALID_TIME_ORDER")


def _validate_cross_fields(values: dict[str, str], errors: list[str]) -> None:
    expected_config = (
        "INVALID"
        if "INVALID"
        in {
            values.get("POLICY_STATUS"),
            values.get("SOURCES_STATUS"),
            values.get("STATE_MAP_STATUS"),
        }
        else "VALID"
    )
    if values.get("CONFIG_STATUS") != expected_config:
        errors.append("CONFIG_STATUS_MISMATCH")
    expected_mode = (
        "INDEX_CONTENT_BOUNDED"
        if values.get("LOCAL_VERSIONING") in {"GIT", "NO_COMMIT"}
        else "TREE_CONTENT_BOUNDED"
    )
    if values.get("LOCAL_FINGERPRINT_MODE") != expected_mode:
        errors.append("LOCAL_FINGERPRINT_MODE_MISMATCH")
    if values.get("OBSERVATION_BOUNDARY") != "FINAL_PROBES_BEFORE_RECEIPT_PUBLICATION":
        errors.append("INVALID_OBSERVATION_BOUNDARY")
    decision = values.get("HUMAN_DECISION")
    reason = values.get("DECISION_REASON")
    if (decision == "NONE") != (reason == "NONE"):
        errors.append("DECISION_REASON_MISMATCH")


def _expect(
    values: dict[str, str], field: str, allowed: set[str], errors: list[str]
) -> None:
    if field in values and values[field] not in allowed:
        errors.append(f"INVALID_VALUE:{field}")


def _integer_in_range(value: str | None, *, minimum: int, maximum: int) -> bool:
    try:
        parsed = int(value or "")
    except ValueError:
        return False
    return minimum <= parsed <= maximum


def _safe_text(value: str, *, maximum: int) -> bool:
    return (
        bool(value)
        and len(value) <= maximum
        and not any(character in value for character in "\r\n\0")
    )

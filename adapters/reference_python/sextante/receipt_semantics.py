from __future__ import annotations

import hashlib
import re

from .authority import is_actor, is_human_actor, is_mother_session_actor
from .evaluation import expected_target_where
from .observations import ALIGNING_EVIDENCE_LEVELS, CAPABILITY_STATES
from .receipt_schema import BOOLEAN_VALUES, HEX_64, parse_utc
from .remote_probe import OID_PATTERN, classify_http_endpoint, remote_source_id


def validate_semantics(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    _validate_capabilities(values, errors)
    _validate_target(values, errors)
    _validate_authority(values, errors)
    local_changed, adapter_changed, version_changed = _validate_change_trace(
        values, errors
    )
    _validate_workspace_identity(values, errors)
    _validate_lifecycle(values, errors)
    _validate_local(values, local_changed=local_changed, errors=errors)
    _validate_remote(values, errors)
    _validate_runtime(values, errors)
    _validate_freshness(values, errors)
    _validate_verdict_and_gates(
        values,
        local_changed=local_changed,
        adapter_changed=adapter_changed,
        version_changed=version_changed,
        errors=errors,
    )
    return errors


def _validate_capabilities(values: dict[str, str], errors: list[str]) -> None:
    entry_keys = sorted(
        key for key in values if re.fullmatch(r"CAPABILITY_[0-9]{3}", key)
    )
    try:
        expected_count = int(values.get("CAPABILITY_COUNT", "-1"))
    except ValueError:
        expected_count = -1
    expected_keys = [
        f"CAPABILITY_{index:03d}" for index in range(1, max(expected_count, 0) + 1)
    ]
    if entry_keys != expected_keys:
        errors.append("CAPABILITY_KEYS_MISMATCH")

    entries: list[str] = []
    states: list[str] = []
    for key in entry_keys:
        entry = values[key]
        parts = entry.split("|")
        if (
            len(parts) != 4
            or not parts[0]
            or not parts[1]
            or parts[2] not in CAPABILITY_STATES
        ):
            errors.append(f"INVALID_CAPABILITY:{key}")
        else:
            states.append(parts[2])
        entries.append(entry)
    expected_hash = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
    if values.get("CAPABILITIES_HASH") != expected_hash:
        errors.append("CAPABILITIES_HASH_MISMATCH")
    if entries != sorted(set(entries)):
        errors.append("CAPABILITIES_NOT_NORMALIZED")

    evidence = values.get("CAPABILITIES_EVIDENCE_LEVEL")
    expected_source = (
        "NOT_PROVIDED"
        if not entries
        else ("HUMAN_INPUT" if evidence == "HUMAN_PROVIDED" else "HARNESS_CONTEXT")
    )
    if values.get("CAPABILITIES_SOURCE") != expected_source:
        errors.append("CAPABILITIES_SOURCE_MISMATCH")

    if not entries:
        base_result, base_state = "PARTIAL", "NOT_PROVIDED"
        if evidence != "UNKNOWN":
            errors.append("EMPTY_CAPABILITIES_WITH_CLAIMED_EVIDENCE")
    elif "UNKNOWN" in states:
        base_result, base_state = "PARTIAL", "INCOMPLETE"
    elif evidence not in ALIGNING_EVIDENCE_LEVELS:
        base_result, base_state = "PARTIAL", "EVIDENCE_UNVERIFIED"
    else:
        base_result, base_state = "ALIGNED", "INVENTORIED"

    observed = (
        values.get("CAPABILITIES"),
        values.get("CAPABILITIES_STATE"),
    )
    if base_result == "PARTIAL":
        allowed = {("PARTIAL", base_state)}
    else:
        allowed = {
            ("ALIGNED", "INVENTORIED"),
            ("DRIFT", "INVENTORIED"),
            ("STALE", "EVIDENCE_EXPIRED"),
        }
    if observed not in allowed:
        errors.append("CAPABILITIES_RESULT_STATE_MISMATCH")


def _validate_workspace_identity(values: dict[str, str], errors: list[str]) -> None:
    workspace_path = values.get("WORKSPACE_PATH", "")
    expected = hashlib.sha256(workspace_path.encode("utf-8")).hexdigest()[:16]
    if values.get("WORKSPACE_ID") != expected:
        errors.append("WORKSPACE_ID_MISMATCH")


def _validate_lifecycle(values: dict[str, str], errors: list[str]) -> None:
    lifecycle = values.get("LIFECYCLE")
    component_statuses = (
        values.get("POLICY_STATUS"),
        values.get("SOURCES_STATUS"),
        values.get("STATE_MAP_STATUS"),
    )
    if lifecycle == "NOT_ADOPTED" and component_statuses != (
        "ABSENT",
        "ABSENT",
        "ABSENT",
    ):
        errors.append("NOT_ADOPTED_COMPONENT_STATUS_MISMATCH")
    if lifecycle == "INVALID" and component_statuses != (
        "INVALID",
        "INVALID",
        "INVALID",
    ):
        errors.append("INVALID_LIFECYCLE_COMPONENT_STATUS_MISMATCH")


def _validate_local(
    values: dict[str, str],
    *,
    local_changed: bool,
    errors: list[str],
) -> None:
    result = values.get("LOCAL")
    versioning = values.get("LOCAL_VERSIONING")
    scan_status = values.get("LOCAL_SCAN_STATUS")
    evidence = values.get("LOCAL_EVIDENCE_LEVEL")
    expected_source = (
        "GIT_QUERY" if versioning in {"GIT", "NO_COMMIT"} else "WORKSPACE_METADATA"
    )
    if values.get("LOCAL_SOURCE") != expected_source:
        errors.append("LOCAL_SOURCE_MISMATCH")
    if evidence != "VERIFIED_DIRECT":
        errors.append("LOCAL_EVIDENCE_MISMATCH")

    commit = values.get("LOCAL_COMMIT", "")
    if versioning == "GIT" and not OID_PATTERN.fullmatch(commit):
        errors.append("LOCAL_GIT_COMMIT_INVALID")
    elif versioning == "NO_COMMIT" and commit != "NO_COMMIT":
        errors.append("LOCAL_NO_COMMIT_MISMATCH")
    elif versioning in {"UNVERSIONED", "UNKNOWN"} and commit != "NOT_APPLICABLE":
        errors.append("LOCAL_NON_GIT_COMMIT_MISMATCH")

    if result in {"ALIGNED", "DRIFT"} and (
        scan_status != "COMPLETE" or local_changed or versioning == "UNKNOWN"
    ):
        errors.append("LOCAL_RESULT_SOURCE_MISMATCH")
    if result == "PARTIAL" and scan_status == "COMPLETE" and versioning != "UNKNOWN":
        errors.append("LOCAL_PARTIAL_WITH_COMPLETE_SOURCE")
    if result == "STALE" and not local_changed:
        errors.append("LOCAL_STALE_WITHOUT_CHANGE")
    if result == "NOT_APPLICABLE":
        errors.append("LOCAL_NOT_APPLICABLE_INVALID")


def _validate_remote(values: dict[str, str], errors: list[str]) -> None:
    result = values.get("REMOTE")
    state = values.get("REMOTE_STATE")
    attempted = values.get("REMOTE_QUERY_ATTEMPTED") == "TRUE"
    evidence = values.get("REMOTE_EVIDENCE_LEVEL")
    source_id = values.get("REMOTE_SOURCE_ID", "")
    ref = values.get("REMOTE_REF", "")
    commit = values.get("REMOTE_COMMIT", "")

    resolved_source = source_id.startswith("sha256:")
    if resolved_source:
        if ref in {"", "UNKNOWN", "NOT_APPLICABLE"} or values.get("REMOTE_NAME") in {
            "",
            "NONE",
        }:
            errors.append("REMOTE_RESOLVED_SOURCE_INCOMPLETE")
        endpoint = classify_http_endpoint(values.get("REMOTE_URL", ""))
        if endpoint.status != "SAFE":
            errors.append("REMOTE_SOURCE_URL_NOT_SAFE")
        else:
            expected_source_id = remote_source_id(
                workspace_path=values.get("WORKSPACE_PATH", ""),
                remote_name=values.get("REMOTE_NAME", ""),
                query_url=endpoint.query_url,
                remote_ref=ref,
            )
            if source_id != expected_source_id:
                errors.append("REMOTE_SOURCE_ID_MISMATCH")

    if result in {"ALIGNED", "DRIFT"}:
        if (
            state != "VERIFIED"
            or not attempted
            or evidence != "VERIFIED_DIRECT"
            or not resolved_source
            or not OID_PATTERN.fullmatch(commit)
            or ref in {"", "UNKNOWN", "NOT_APPLICABLE"}
            or values.get("REMOTE_NAME") in {"", "NONE"}
        ):
            errors.append("REMOTE_VERIFIED_RESULT_MISMATCH")
    elif result == "NOT_APPLICABLE":
        if (
            state not in {"NO_GIT", "NO_REMOTE"}
            or attempted
            or evidence != "VERIFIED_DIRECT"
            or source_id != "NOT_APPLICABLE"
            or ref != "NOT_APPLICABLE"
            or values.get("REMOTE_NAME") != "NONE"
        ):
            errors.append("REMOTE_NOT_APPLICABLE_MISMATCH")
    elif result == "STALE":
        if state != "EVIDENCE_EXPIRED" or evidence != "VERIFIED_DIRECT":
            errors.append("REMOTE_STALE_MISMATCH")
        elif resolved_source:
            if not attempted or not OID_PATTERN.fullmatch(commit):
                errors.append("REMOTE_STALE_VERIFIED_SOURCE_MISMATCH")
        elif not (
            source_id == "NOT_APPLICABLE" and ref == "NOT_APPLICABLE" and not attempted
        ):
            errors.append("REMOTE_STALE_SOURCE_MISMATCH")
    elif result == "PARTIAL":
        if state in {"VERIFIED", "EVIDENCE_EXPIRED"}:
            errors.append("REMOTE_PARTIAL_STATE_MISMATCH")
        if source_id == "NOT_APPLICABLE" and state not in {"NO_GIT", "NO_REMOTE"}:
            errors.append("REMOTE_PARTIAL_SOURCE_MISMATCH")
        if resolved_source and evidence != "VERIFIED_DIRECT":
            errors.append("REMOTE_RESOLVED_WITH_WEAK_EVIDENCE")


def _validate_runtime(values: dict[str, str], errors: list[str]) -> None:
    result = values.get("RUNTIME")
    state = values.get("RUNTIME_STATE")
    target = values.get("RUNTIME_TARGET", "")
    source = values.get("RUNTIME_SOURCE", "")
    evidence = values.get("RUNTIME_EVIDENCE_LEVEL")
    source_is_concrete = source not in {"", "NOT_PROVIDED"}
    target_is_concrete = target not in {
        "",
        "UNKNOWN",
        "NOT_APPLICABLE",
        "UNAVAILABLE",
    }

    if result in {"ALIGNED", "DRIFT"}:
        if (
            state != "VERIFIED"
            or not source_is_concrete
            or not target_is_concrete
            or evidence not in ALIGNING_EVIDENCE_LEVELS
        ):
            errors.append("RUNTIME_VERIFIED_RESULT_MISMATCH")
    elif result == "NOT_APPLICABLE":
        if (
            state not in {"NOT_APPLICABLE", "NO_RUNTIME"}
            or target != "NOT_APPLICABLE"
            or not source_is_concrete
            or evidence not in ALIGNING_EVIDENCE_LEVELS
        ):
            errors.append("RUNTIME_NOT_APPLICABLE_MISMATCH")
    elif result == "STALE":
        if (
            state != "EVIDENCE_EXPIRED"
            or not source_is_concrete
            or target in {"", "UNKNOWN", "UNAVAILABLE"}
            or evidence not in ALIGNING_EVIDENCE_LEVELS
        ):
            errors.append("RUNTIME_STALE_MISMATCH")
    elif result == "PARTIAL" and state in {"VERIFIED", "EVIDENCE_EXPIRED"}:
        errors.append("RUNTIME_PARTIAL_STATE_MISMATCH")


def _validate_target(values: dict[str, str], errors: list[str]) -> None:
    status = values.get("TARGET")
    where = values.get("TARGET_WHERE")
    action = values.get("TARGET_ACTION")
    actor = values.get("TARGET_CONFIRMED_BY")
    if status == "CONFIRMED":
        if (
            not where
            or action not in {"EDIT", "PUSH", "DEPLOY"}
            or not is_human_actor(actor or "")
        ):
            errors.append("INVALID_CONFIRMED_TARGET")
    elif status == "UNCONFIRMED" and (where, action, actor) != (
        "UNCONFIRMED",
        "UNCONFIRMED",
        "UNCONFIRMED",
    ):
        errors.append("INVALID_UNCONFIRMED_TARGET")
    if values.get("INTENT") == "read" and status != "UNCONFIRMED":
        errors.append("READ_WITH_CONFIRMED_TARGET")


def _validate_authority(values: dict[str, str], errors: list[str]) -> None:
    policy = values.get("README_POLICY")
    policy_actor = values.get("README_POLICY_CONFIRMED_BY", "")
    if policy_actor != "UNCONFIRMED" and not is_human_actor(policy_actor):
        errors.append("INVALID_README_POLICY_AUTHOR")
    if policy != "IGNORE" and (
        not is_human_actor(policy_actor)
        or values.get("README_POLICY_SOURCE") != "SESSION_HUMAN"
    ):
        errors.append("README_TRUST_WITHOUT_HUMAN")
    remote_actor = values.get("REMOTE_QUERY_CONFIRMED_BY", "")
    confirmed_source = values.get("REMOTE_QUERY_CONFIRMED_SOURCE_ID", "")
    source_id = values.get("REMOTE_SOURCE_ID", "")
    actor_is_unconfirmed = remote_actor == "UNCONFIRMED"
    source_is_unconfirmed = confirmed_source == "UNCONFIRMED"
    if actor_is_unconfirmed != source_is_unconfirmed:
        errors.append("REMOTE_CONFIRMATION_PAIR_MISMATCH")
    if not actor_is_unconfirmed and not is_human_actor(remote_actor):
        errors.append("INVALID_REMOTE_QUERY_AUTHOR")
    if values.get("REMOTE_STATE") == "NETWORK_CONFIRMATION_REQUIRED" and (
        not actor_is_unconfirmed or not source_is_unconfirmed
    ):
        errors.append("REMOTE_CONFIRMATION_STATE_MISMATCH")
    attempted = values.get("REMOTE_QUERY_ATTEMPTED") == "TRUE"
    if attempted and (
        not is_human_actor(remote_actor) or confirmed_source != source_id
    ):
        errors.append("REMOTE_QUERY_WITHOUT_MATCHING_CONFIRMATION")
    if values.get("REMOTE_STATE") == "VERIFIED" and not attempted:
        errors.append("VERIFIED_REMOTE_WITHOUT_QUERY")
    if values.get("REMOTE_STATE") == "SOURCE_CONFIRMATION_MISMATCH" and (
        attempted or not is_human_actor(remote_actor) or confirmed_source == source_id
    ):
        errors.append("REMOTE_SOURCE_MISMATCH_STATE_INVALID")
    target_actor = values.get("TARGET_CONFIRMED_BY")
    decided_by = values.get("DECIDED_BY")
    if values.get("TARGET") == "CONFIRMED" and decided_by != target_actor:
        errors.append("TARGET_DECISION_AUTHOR_MISMATCH")
    if decided_by != "NONE" and not is_human_actor(decided_by or ""):
        errors.append("INVALID_DECISION_AUTHOR")
    if not is_actor(values.get("COLLECTED_BY", "")):
        errors.append("INVALID_AUTHOR:COLLECTED_BY")
    if not is_mother_session_actor(values.get("SYNTHESIZED_BY", "")):
        errors.append("INVALID_AUTHOR:SYNTHESIZED_BY")


def _validate_change_trace(
    values: dict[str, str], errors: list[str]
) -> tuple[bool, bool, bool]:
    local_finished = values.get("LOCAL_FINGERPRINT_FINISHED")
    detectable_local_change = (
        local_finished == "UNAVAILABLE"
        or values.get("LOCAL_FINGERPRINT_STARTED") != local_finished
    )
    local_changed = _boolean(values.get("LOCAL_CHANGED_DURING_CHECK")) is True
    if detectable_local_change and not local_changed:
        errors.append("LOCAL_CHANGE_TRACE_MISMATCH")
    if (
        local_finished != "UNAVAILABLE"
        and values.get("LOCAL_FINGERPRINT") != local_finished
    ):
        errors.append("LOCAL_FINAL_FINGERPRINT_MISMATCH")

    adapter_finished = values.get("ADAPTER_FINGERPRINT_FINISHED")
    adapter_changed = (
        adapter_finished == "UNAVAILABLE"
        or values.get("ADAPTER_FINGERPRINT_STARTED") != adapter_finished
    )
    if _boolean(values.get("ADAPTER_CHANGED_DURING_CHECK")) != adapter_changed:
        errors.append("ADAPTER_CHANGE_TRACE_MISMATCH")
    final_complete = bool(adapter_finished and HEX_64.fullmatch(adapter_finished))
    if (values.get("ADAPTER_FINAL_STATUS") == "COMPLETE") != final_complete:
        errors.append("ADAPTER_FINAL_STATUS_MISMATCH")
    version_changed = values.get("SKILL_VERSION") != values.get(
        "SKILL_VERSION_FINISHED"
    )
    return local_changed, adapter_changed, version_changed


def _validate_freshness(values: dict[str, str], errors: list[str]) -> None:
    finished = parse_utc(values.get("FINISHED_AT_UTC", ""))
    if finished is None:
        return
    for prefix in ("REMOTE", "RUNTIME", "CAPABILITIES"):
        observed = parse_utc(values.get(f"{prefix}_OBSERVED_AT_UTC", ""))
        try:
            max_age = int(values.get(f"{prefix}_MAX_AGE_SECONDS", "0"))
        except ValueError:
            continue
        if observed is None or max_age <= 0:
            continue
        age = (finished - observed).total_seconds()
        result = values.get(prefix)
        state = values.get(f"{prefix}_STATE")
        if result in {"ALIGNED", "DRIFT", "NOT_APPLICABLE"} and (
            age > max_age or age < -300
        ):
            errors.append(f"FRESHNESS_RESULT_MISMATCH:{prefix}")
        if (
            result == "STALE"
            and state == "EVIDENCE_EXPIRED"
            and (-300 <= age <= max_age)
        ):
            errors.append(f"FRESHNESS_STATE_MISMATCH:{prefix}")


def _validate_verdict_and_gates(
    values: dict[str, str],
    *,
    local_changed: bool,
    adapter_changed: bool,
    version_changed: bool,
    errors: list[str],
) -> None:
    results = [
        values.get("LOCAL"),
        values.get("REMOTE"),
        values.get("RUNTIME"),
        values.get("CAPABILITIES"),
    ]
    if local_changed or adapter_changed or version_changed or "STALE" in results:
        expected_verdict = "STALE"
    elif "DRIFT" in results:
        expected_verdict = "DRIFT"
    elif (
        "PARTIAL" in results
        or values.get("CONFIG_STATUS") == "INVALID"
        or (
            values.get("LIFECYCLE") == "ADOPTED"
            and values.get("STATE_MAP_STATUS") != "LOADED"
        )
    ):
        expected_verdict = "PARTIAL"
    else:
        expected_verdict = "ALIGNED"
    if values.get("STATE_VERDICT") != expected_verdict:
        errors.append("STATE_VERDICT_MISMATCH")
    expected_read_gate = "PASS" if expected_verdict == "ALIGNED" else "WARN"
    if values.get("READ_GATE") != expected_read_gate:
        errors.append("READ_GATE_MISMATCH")
    if values.get("WRITE_GATE") != _expected_write_gate(values):
        errors.append("WRITE_GATE_MISMATCH")


def _expected_write_gate(values: dict[str, str]) -> str:
    intent = values.get("INTENT")
    expected_action = str(intent).upper()
    required_target_where = expected_target_where(
        intent=str(intent),
        remote_name=values.get("REMOTE_NAME", ""),
        remote_ref=values.get("REMOTE_REF", ""),
        runtime_target=values.get("RUNTIME_TARGET", ""),
    )
    baseline_ready = values.get("LIFECYCLE") == "NOT_ADOPTED" or (
        values.get("LIFECYCLE") == "ADOPTED"
        and values.get("STATE_MAP_STATUS") == "LOADED"
    )
    if (
        intent == "read"
        or values.get("STATE_VERDICT") == "STALE"
        or not baseline_ready
        or values.get("CONFIG_STATUS") != "VALID"
        or values.get("TARGET") != "CONFIRMED"
        or values.get("TARGET_WHERE") != required_target_where
        or values.get("TARGET_ACTION") != expected_action
        or values.get("LOCAL") != "ALIGNED"
        or values.get("CAPABILITIES") != "ALIGNED"
    ):
        return "BLOCK"
    if intent == "edit":
        return "PASS"
    if intent == "push":
        return "PASS" if values.get("REMOTE") == "ALIGNED" else "BLOCK"
    if intent == "deploy":
        return (
            "PASS"
            if values.get("REMOTE") in {"ALIGNED", "NOT_APPLICABLE"}
            and values.get("RUNTIME") == "ALIGNED"
            else "BLOCK"
        )
    return "BLOCK"


def _boolean(value: str | None) -> bool | None:
    if value not in BOOLEAN_VALUES:
        return None
    return value == "TRUE"

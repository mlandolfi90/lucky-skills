from __future__ import annotations

from dataclasses import replace

from .authority import is_human_actor
from .observations import ALIGNING_EVIDENCE_LEVELS


def apply_state_map(*, local, remote, runtime, capabilities, state_map):
    expected_local_commit = state_map.get("GIT_LOCAL_COMMIT", "UNKNOWN")
    expected_local_fingerprint = state_map.get("GIT_LOCAL_FINGERPRINT", "UNKNOWN")
    if local.result == "ALIGNED" and _known(expected_local_fingerprint):
        if expected_local_fingerprint != local.fingerprint:
            local = replace(local, result="DRIFT")
    elif (
        local.result == "ALIGNED"
        and _known(expected_local_commit)
        and expected_local_commit != local.head
    ):
        local = replace(local, result="DRIFT")

    expected_remote_commit = state_map.get("GIT_REMOTE_COMMIT", "UNKNOWN")
    expected_remote_ref = state_map.get("GIT_REMOTE_REF", "UNKNOWN")
    remote_expectation = _known(expected_remote_ref) or _known(expected_remote_commit)
    if remote_expectation and (
        remote.state != "VERIFIED"
        or remote.evidence_level not in ALIGNING_EVIDENCE_LEVELS
    ):
        if remote.result != "STALE":
            remote = replace(remote, result="PARTIAL")
    else:
        if _known(expected_remote_ref) and remote.ref != expected_remote_ref:
            remote = replace(remote, result="DRIFT")
        if _known(expected_remote_commit) and remote.head != expected_remote_commit:
            remote = replace(remote, result="DRIFT")

    expected_runtime_version = state_map.get("RUNTIME_VERSION", "UNKNOWN")
    if _known(expected_runtime_version):
        if (
            runtime.state != "VERIFIED"
            or runtime.evidence_level not in ALIGNING_EVIDENCE_LEVELS
        ):
            if runtime.result != "STALE":
                runtime = replace(runtime, result="PARTIAL")
        elif runtime.version != expected_runtime_version:
            runtime = replace(runtime, result="DRIFT")

    expected_capabilities_hash = state_map.get("CAPABILITIES_HASH", "UNKNOWN")
    if _known(expected_capabilities_hash) and capabilities.entries:
        if (
            capabilities.state != "INVENTORIED"
            or capabilities.evidence_level not in ALIGNING_EVIDENCE_LEVELS
        ):
            if capabilities.result != "STALE":
                capabilities = replace(capabilities, result="PARTIAL")
        elif capabilities.fingerprint != expected_capabilities_hash:
            capabilities = replace(capabilities, result="DRIFT")
    return local, remote, runtime, capabilities


def state_verdict(
    source_results: list[str],
    *,
    additional_partial: bool = False,
    additional_stale: bool = False,
) -> str:
    if additional_stale or "STALE" in source_results:
        return "STALE"
    if "DRIFT" in source_results:
        return "DRIFT"
    if additional_partial or "PARTIAL" in source_results:
        return "PARTIAL"
    return "ALIGNED"


def target(
    *,
    intent: str,
    where: str,
    action: str,
    confirmed_by: str,
) -> tuple[str, dict[str, str]]:
    values = (where, action, confirmed_by)
    if intent == "read" and any(values):
        raise ValueError("una consulta read debe mantener TARGET=UNCONFIRMED")
    if all(values):
        if not is_human_actor(confirmed_by):
            raise ValueError("TARGET_CONFIRMED_BY debe identificar un actor human:")
        return "CONFIRMED", {
            "where": where,
            "action": action,
            "confirmed_by": confirmed_by,
        }
    if any(values):
        raise ValueError("TARGET requiere WHERE, ACTION y CONFIRMED_BY")
    return "UNCONFIRMED", {
        "where": "UNCONFIRMED",
        "action": "UNCONFIRMED",
        "confirmed_by": "UNCONFIRMED",
    }


def decision_actor(
    *,
    target_status: str,
    target_confirmed_by: str,
    declared_actor: str,
) -> str:
    if target_status == "CONFIRMED":
        if declared_actor == "NONE":
            return target_confirmed_by
        if declared_actor != target_confirmed_by:
            raise ValueError("DECIDED_BY debe coincidir con TARGET_CONFIRMED_BY")
    if declared_actor != "NONE" and not is_human_actor(declared_actor):
        raise ValueError("DECIDED_BY debe identificar un actor human:")
    return declared_actor


def write_gate(
    *,
    intent: str,
    target_status: str,
    target_where: str,
    expected_target_where: str,
    target_action: str,
    baseline_ready: bool,
    config_valid: bool,
    state_verdict: str,
    local_result: str,
    remote_result: str,
    runtime_result: str,
    capabilities_result: str,
) -> str:
    if (
        state_verdict == "STALE"
        or not baseline_ready
        or not config_valid
        or target_status != "CONFIRMED"
        or target_where != expected_target_where
        or target_action.lower() != intent
        or local_result != "ALIGNED"
        or capabilities_result != "ALIGNED"
    ):
        return "BLOCK"
    if intent == "edit":
        return "PASS"
    if intent == "push":
        return "PASS" if remote_result == "ALIGNED" else "BLOCK"
    if intent == "deploy":
        return (
            "PASS"
            if remote_result in {"ALIGNED", "NOT_APPLICABLE"}
            and runtime_result == "ALIGNED"
            else "BLOCK"
        )
    return "BLOCK"


def next_decision(
    *,
    intent: str,
    target_status: str,
    target_where: str,
    expected_target_where: str,
    target_action: str,
    baseline_ready: bool,
    config_valid: bool,
    changed_during_check: bool,
    local_result: str,
    remote_state: str,
    runtime_state: str,
    remote_result: str,
    runtime_result: str,
    capabilities_result: str,
) -> tuple[str, str]:
    if changed_during_check:
        return "STOP", "LOCAL_OR_ADAPTER_CHANGED_DURING_CHECK"
    if remote_state in {"MULTIPLE_CANDIDATES", "UNKNOWN_SELECTION"}:
        return "CHOOSE_SOURCE", f"REMOTE_{remote_state}"
    if remote_state == "NETWORK_CONFIRMATION_REQUIRED":
        return "CONFIRM_SOURCE_ACCESS", "REMOTE_NETWORK_ACCESS_REQUIRED"
    if remote_state == "SOURCE_CONFIRMATION_MISMATCH":
        return "CONFIRM_SOURCE_ACCESS", "REMOTE_SOURCE_CHANGED"
    if runtime_state == "MULTIPLE_CANDIDATES":
        return "CHOOSE_SOURCE", "RUNTIME_MULTIPLE_CANDIDATES"
    if intent != "read" and not baseline_ready:
        return "STOP", "STATE_MAP_NOT_CORROBORATED"
    if intent != "read" and local_result != "ALIGNED":
        return "STOP", "LOCAL_NOT_ALIGNED"
    if intent != "read" and not config_valid:
        return "STOP", "CONFIG_INVALID"
    if intent != "read" and capabilities_result != "ALIGNED":
        return "STOP", "CAPABILITIES_NOT_VERIFIED"
    if intent != "read" and target_status != "CONFIRMED":
        return "CONFIRM_TARGET", "WRITE_ACTION_PENDING"
    if intent != "read" and target_action.lower() != intent:
        return "CONFIRM_TARGET", "TARGET_ACTION_MISMATCH"
    if intent != "read" and target_where != expected_target_where:
        return "CONFIRM_TARGET", "TARGET_WHERE_MISMATCH"
    if intent == "push" and remote_result != "ALIGNED":
        return "PROVIDE_ACCESS", "REMOTE_NOT_VERIFIED"
    if intent == "deploy" and runtime_result != "ALIGNED":
        return "PROVIDE_ACCESS", "RUNTIME_NOT_VERIFIED"
    return "NONE", "NONE"


def expected_target_where(
    *,
    intent: str,
    remote_name: str,
    remote_ref: str,
    runtime_target: str,
) -> str:
    if intent == "edit":
        return "local:workspace"
    if intent == "push":
        if remote_name in {"", "NONE"} or remote_ref in {
            "",
            "UNKNOWN",
            "NOT_APPLICABLE",
        }:
            return "UNAVAILABLE"
        return f"remote:{remote_name}:{remote_ref}"
    if intent == "deploy":
        return runtime_target or "UNAVAILABLE"
    return "UNCONFIRMED"


def changed_during_check(
    started,
    finished,
    version_started: str,
    version_finished: str,
    adapter_started: str,
    adapter_finished: str,
):
    return (
        started.fingerprint != finished.fingerprint
        or started.head != finished.head
        or started.branch != finished.branch
        or version_started != version_finished
        or adapter_started != adapter_finished
    )


def _known(value: str | None) -> bool:
    if not value:
        return False
    return value.upper() not in {
        "UNKNOWN",
        "N/D",
        "NOT_APPLICABLE",
    }

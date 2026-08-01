from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    CapabilitiesObservation,
    LocalObservation,
    RemoteObservation,
    RuntimeObservation,
)


@dataclass(frozen=True)
class ReceiptAssembly:
    workspace: Path
    skill_version: str
    skill_version_source: str
    skill_version_finished: str
    harness: str
    execution_level: str
    intent: str
    started_at: str
    finished_at: str
    lifecycle_status: str
    config_status: str
    policy_status: str
    sources_status: str
    state_map_status: str
    readme_policy: str
    readme_policy_source: str
    readme_policy_confirmed_by: str
    local: LocalObservation
    local_fingerprint_started: str
    local_fingerprint_finished: str
    local_changed_during_check: bool
    local_observed_at: str
    adapter_fingerprint_started: str
    adapter_fingerprint_finished: str
    adapter_final_status: str
    adapter_changed_during_check: bool
    remote: RemoteObservation
    remote_query_confirmed_by: str
    remote_query_confirmed_source_id: str
    remote_max_age_seconds: int
    remote_observed_at: str
    runtime: RuntimeObservation
    runtime_candidates: tuple[str, ...]
    runtime_max_age_seconds: int
    runtime_observed_at: str
    capabilities: CapabilitiesObservation
    capabilities_max_age_seconds: int
    capabilities_observed_at: str
    state_verdict: str
    read_gate: str
    write_gate: str
    target_status: str
    target_fields: dict[str, str]
    human_decision: str
    decision_reason: str
    collected_by: str
    synthesized_by: str
    decided_by: str


def build_receipt_values(data: ReceiptAssembly) -> dict[str, object]:
    workspace_id = hashlib.sha256(str(data.workspace).encode("utf-8")).hexdigest()[:16]
    receipt_id = (
        f"sextante-{compact_timestamp(data.finished_at)}-"
        f"{data.local.fingerprint[:8]}"
    )
    values: dict[str, object] = {
        "RECEIPT_SCHEMA": "1",
        "RECEIPT_ID": receipt_id,
        "SKILL_VERSION": data.skill_version,
        "SKILL_VERSION_SOURCE": data.skill_version_source,
        "SKILL_VERSION_FINISHED": data.skill_version_finished,
        "CONTRACT_VERSION": "1",
        "ADAPTER_ID": "reference-python",
        "ADAPTER_VERSION": data.skill_version,
        "HARNESS": data.harness,
        "EXECUTION_LEVEL": data.execution_level,
        "INTENT": data.intent,
        "STARTED_AT_UTC": data.started_at,
        "FINISHED_AT_UTC": data.finished_at,
        "WORKSPACE_ID": workspace_id,
        "WORKSPACE_PATH": str(data.workspace),
        "LIFECYCLE": data.lifecycle_status,
        "CONFIG_STATUS": data.config_status,
        "POLICY_STATUS": data.policy_status,
        "SOURCES_STATUS": data.sources_status,
        "STATE_MAP_STATUS": data.state_map_status,
        "README_POLICY": data.readme_policy,
        "README_POLICY_SOURCE": data.readme_policy_source,
        "README_POLICY_CONFIRMED_BY": data.readme_policy_confirmed_by,
        "LOCAL": data.local.result,
        "LOCAL_VERSIONING": data.local.versioning,
        "LOCAL_SOURCE": (
            "GIT_QUERY"
            if data.local.versioning in {"GIT", "NO_COMMIT"}
            else "WORKSPACE_METADATA"
        ),
        "LOCAL_EVIDENCE_LEVEL": "VERIFIED_DIRECT",
        "LOCAL_FINGERPRINT_MODE": (
            "INDEX_CONTENT_BOUNDED"
            if data.local.versioning in {"GIT", "NO_COMMIT"}
            else "TREE_CONTENT_BOUNDED"
        ),
        "LOCAL_FINGERPRINT": data.local.fingerprint,
        "LOCAL_FINGERPRINT_STARTED": data.local_fingerprint_started,
        "LOCAL_FINGERPRINT_FINISHED": data.local_fingerprint_finished,
        "LOCAL_CHANGED_DURING_CHECK": str(data.local_changed_during_check).upper(),
        "LOCAL_COMMIT": data.local.head,
        "LOCAL_BRANCH": data.local.branch,
        "LOCAL_DIRTY": str(data.local.dirty).upper(),
        "LOCAL_DIRTY_MODE": "RAW_NO_FILTERS_CONSERVATIVE",
        "LOCAL_DIRTY_COUNT": str(data.local.dirty_count),
        "LOCAL_ENTRY_COUNT": str(data.local.entry_count),
        "LOCAL_SCAN_STATUS": data.local.scan_status,
        "LOCAL_GIT_SAFE_OVERRIDE": (
            "PER_COMMAND" if data.local.git_safe_override else "NOT_REQUIRED"
        ),
        "LOCAL_OBSERVED_AT_UTC": data.local_observed_at,
        "ADAPTER_FINGERPRINT_STARTED": data.adapter_fingerprint_started,
        "ADAPTER_FINGERPRINT_FINISHED": data.adapter_fingerprint_finished,
        "ADAPTER_FINAL_STATUS": data.adapter_final_status,
        "ADAPTER_CHANGED_DURING_CHECK": str(data.adapter_changed_during_check).upper(),
        "OBSERVATION_BOUNDARY": "FINAL_PROBES_BEFORE_RECEIPT_PUBLICATION",
        "REMOTE": data.remote.result,
        "REMOTE_STATE": data.remote.state,
        "REMOTE_NAME": data.remote.name,
        "REMOTE_URL": data.remote.url,
        "REMOTE_COMMIT": data.remote.head,
        "REMOTE_REF": data.remote.ref,
        "REMOTE_SOURCE_ID": data.remote.source_id,
        "REMOTE_QUERY_CONFIRMED_SOURCE_ID": data.remote_query_confirmed_source_id,
        "REMOTE_REDIRECT_POLICY": data.remote.redirect_policy,
        "REMOTE_QUERY_ATTEMPTED": str(data.remote.query_attempted).upper(),
        "REMOTE_CANDIDATES": ",".join(data.remote.candidates),
        "REMOTE_EVIDENCE_LEVEL": data.remote.evidence_level,
        "REMOTE_QUERY_CONFIRMED_BY": data.remote_query_confirmed_by,
        "REMOTE_MAX_AGE_SECONDS": str(data.remote_max_age_seconds),
        "REMOTE_OBSERVED_AT_UTC": data.remote_observed_at,
        "RUNTIME": data.runtime.result,
        "RUNTIME_STATE": data.runtime.state,
        "RUNTIME_VERSION": data.runtime.version,
        "RUNTIME_TARGET": data.runtime.target,
        "RUNTIME_SOURCE": data.runtime.source,
        "RUNTIME_CANDIDATES": ",".join(data.runtime_candidates),
        "RUNTIME_MAX_AGE_SECONDS": str(data.runtime_max_age_seconds),
        "RUNTIME_EVIDENCE_LEVEL": data.runtime.evidence_level,
        "RUNTIME_OBSERVED_AT_UTC": data.runtime_observed_at,
        "CAPABILITIES": data.capabilities.result,
        "CAPABILITIES_STATE": data.capabilities.state,
        "CAPABILITIES_HASH": data.capabilities.fingerprint,
        "CAPABILITIES_SOURCE": (
            "HUMAN_INPUT"
            if data.capabilities.evidence_level == "HUMAN_PROVIDED"
            else ("HARNESS_CONTEXT" if data.capabilities.entries else "NOT_PROVIDED")
        ),
        "CAPABILITY_COUNT": str(len(data.capabilities.entries)),
        "CAPABILITIES_MAX_AGE_SECONDS": str(data.capabilities_max_age_seconds),
        "CAPABILITIES_EVIDENCE_LEVEL": data.capabilities.evidence_level,
        "CAPABILITIES_OBSERVED_AT_UTC": data.capabilities_observed_at,
        "STATE_VERDICT": data.state_verdict,
        "READ_GATE": data.read_gate,
        "WRITE_GATE": data.write_gate,
        "TARGET": data.target_status,
        "TARGET_WHERE": data.target_fields["where"],
        "TARGET_ACTION": data.target_fields["action"],
        "TARGET_CONFIRMED_BY": data.target_fields["confirmed_by"],
        "HUMAN_DECISION": data.human_decision,
        "DECISION_REASON": data.decision_reason,
        "COLLECTED_BY": data.collected_by,
        "SYNTHESIZED_BY": data.synthesized_by,
        "DECIDED_BY": data.decided_by,
    }
    for index, entry in enumerate(data.capabilities.entries, start=1):
        values[f"CAPABILITY_{index:03d}"] = entry
    return values


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def compact_timestamp(timestamp: str) -> str:
    return (
        timestamp.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+00:00", "Z")
    )

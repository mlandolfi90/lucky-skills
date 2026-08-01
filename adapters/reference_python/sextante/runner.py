from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .authority import is_human_actor, is_mother_session_actor
from .component_contracts import POLICY_DEFAULTS, POLICY_LIMITS
from .evaluation import (
    apply_state_map,
    changed_during_check,
    decision_actor,
    expected_target_where,
    next_decision,
    state_verdict,
    target,
    write_gate,
)
from .freshness import enforce_freshness
from .identity import adapter_fingerprint
from .local_probe import probe_local
from .models import RuntimeObservation
from .observations import normalize_capabilities, normalize_runtime
from .project_config import (
    csv_values,
    load_project_config,
    positive_int,
    read_version,
    resolve_readme_policy,
)
from .receipt import display_path, write_receipt
from .receipt_contract import ReceiptAssembly, build_receipt_values, utc_now
from .remote_probe import probe_remote, valid_source_id


def run_check(
    *,
    arguments: argparse.Namespace,
    workspace: Path,
    started_at: str,
    skill_version: str,
    skill_version_source: str,
    source_root: Path | None,
    adapter_root: Path,
) -> dict[str, str]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace inexistente o no accesible: {workspace}")
    if arguments.remote_confirmed_by and not is_human_actor(
        arguments.remote_confirmed_by
    ):
        raise ValueError("--remote-confirmed-by debe identificar un actor human:")
    if bool(arguments.remote_confirmed_by) != bool(
        arguments.remote_confirmed_source_id
    ):
        raise ValueError("confirmación remota requiere actor y source-id en conjunto")
    if arguments.remote_confirmed_source_id and not valid_source_id(
        arguments.remote_confirmed_source_id
    ):
        raise ValueError("--remote-confirmed-source-id inválido")
    if not is_mother_session_actor(arguments.synthesized_by):
        raise ValueError("--synthesized-by debe identificar la sesión madre")

    adapter_started = adapter_fingerprint(adapter_root)
    project = load_project_config(workspace)
    (
        readme_policy,
        readme_policy_source,
        readme_policy_confirmed_by,
    ) = resolve_readme_policy(
        arguments.readme_policy,
        arguments.readme_policy_confirmed_by,
    )
    timeout_seconds = _configured_limit(
        explicit=arguments.timeout,
        configured=project.policy.get("COLLECTOR_TIMEOUT_SECONDS"),
        default=POLICY_DEFAULTS["COLLECTOR_TIMEOUT_SECONDS"],
        maximum=POLICY_LIMITS["COLLECTOR_TIMEOUT_SECONDS"],
    )
    max_entries = _configured_limit(
        explicit=arguments.max_entries,
        configured=project.policy.get("WORKSPACE_MAX_ENTRIES"),
        default=POLICY_DEFAULTS["WORKSPACE_MAX_ENTRIES"],
        maximum=POLICY_LIMITS["WORKSPACE_MAX_ENTRIES"],
    )

    local_started, git = probe_local(
        workspace,
        timeout_seconds=timeout_seconds,
        max_entries=max_entries,
    )
    local_observed_at = utc_now()

    remote = probe_remote(
        git=git,
        local=local_started,
        selected_remote=arguments.remote or project.sources.get("REMOTE_NAME", "AUTO"),
        network_confirmed_by=arguments.remote_confirmed_by,
        confirmed_source_id=arguments.remote_confirmed_source_id,
    )
    remote_observed_at = utc_now()
    remote_max_age_seconds = positive_int(
        project.policy.get("REMOTE_MAX_AGE_SECONDS"),
        default=POLICY_DEFAULTS["REMOTE_MAX_AGE_SECONDS"],
        maximum=POLICY_LIMITS["REMOTE_MAX_AGE_SECONDS"],
    )
    remote = enforce_freshness(
        remote,
        remote_observed_at,
        max_age_seconds=remote_max_age_seconds,
    )

    runtime_candidates = csv_values(project.sources.get("RUNTIME_CANDIDATES", ""))
    runtime = _runtime_observation(arguments, project.sources, runtime_candidates)
    runtime_observed_at = arguments.runtime_observed_at or utc_now()
    runtime_max_age_seconds = positive_int(
        project.policy.get("RUNTIME_MAX_AGE_SECONDS"),
        default=POLICY_DEFAULTS["RUNTIME_MAX_AGE_SECONDS"],
        maximum=POLICY_LIMITS["RUNTIME_MAX_AGE_SECONDS"],
    )
    runtime = enforce_freshness(
        runtime,
        runtime_observed_at,
        max_age_seconds=runtime_max_age_seconds,
    )

    capabilities = normalize_capabilities(
        arguments.capability,
        evidence_level=arguments.capabilities_evidence,
    )
    capabilities_observed_at = arguments.capabilities_observed_at or utc_now()
    capabilities_max_age_seconds = positive_int(
        project.policy.get("CAPABILITIES_MAX_AGE_SECONDS"),
        default=POLICY_DEFAULTS["CAPABILITIES_MAX_AGE_SECONDS"],
        maximum=POLICY_LIMITS["CAPABILITIES_MAX_AGE_SECONDS"],
    )
    capabilities = enforce_freshness(
        capabilities,
        capabilities_observed_at,
        max_age_seconds=capabilities_max_age_seconds,
    )

    local, remote, runtime, capabilities = apply_state_map(
        local=local_started,
        remote=remote,
        runtime=runtime,
        capabilities=capabilities,
        state_map=project.state_map,
    )
    (
        local_finished,
        local_finished_fingerprint,
        local_final_available,
    ) = _finish_local(
        workspace,
        local_started,
        timeout_seconds=timeout_seconds,
        max_entries=max_entries,
    )
    version_finished = _finish_version(source_root, skill_version)
    adapter_finished, adapter_final_status = _finish_adapter(adapter_root)
    local_changed = (
        not local_final_available
        or local_started.fingerprint != local_finished.fingerprint
        or local_started.head != local_finished.head
        or local_started.branch != local_finished.branch
    )
    adapter_changed = adapter_started != adapter_finished
    changed = not local_final_available or changed_during_check(
        local_started,
        local_finished,
        skill_version,
        version_finished,
        adapter_started,
        adapter_finished,
    )
    if not local_final_available or local_changed:
        local = replace(local_finished, result="STALE")

    verdict = state_verdict(
        [local.result, remote.result, runtime.result, capabilities.result],
        additional_stale=changed,
        additional_partial=(
            project.status == "INVALID"
            or (project.adopted and project.state_map_status != "LOADED")
        ),
    )
    target_status, target_fields = target(
        intent=arguments.intent,
        where=arguments.target_where,
        action=arguments.target_action,
        confirmed_by=arguments.target_confirmed_by,
    )
    decided_by = decision_actor(
        target_status=target_status,
        target_confirmed_by=target_fields["confirmed_by"],
        declared_actor=arguments.decided_by,
    )
    required_target_where = expected_target_where(
        intent=arguments.intent,
        remote_name=remote.name,
        remote_ref=remote.ref,
        runtime_target=runtime.target,
    )
    read_gate = "PASS" if verdict == "ALIGNED" else "WARN"
    write_gate_value = write_gate(
        intent=arguments.intent,
        target_status=target_status,
        target_where=target_fields["where"],
        expected_target_where=required_target_where,
        target_action=target_fields["action"],
        baseline_ready=project.baseline_ready,
        config_valid=project.status == "VALID",
        state_verdict=verdict,
        local_result=local.result,
        remote_result=remote.result,
        runtime_result=runtime.result,
        capabilities_result=capabilities.result,
    )
    human_decision, decision_reason = next_decision(
        intent=arguments.intent,
        target_status=target_status,
        target_where=target_fields["where"],
        expected_target_where=required_target_where,
        target_action=target_fields["action"],
        baseline_ready=project.baseline_ready,
        config_valid=project.status == "VALID",
        changed_during_check=changed,
        local_result=local.result,
        remote_state=remote.state,
        runtime_state=runtime.state,
        remote_result=remote.result,
        runtime_result=runtime.result,
        capabilities_result=capabilities.result,
    )

    receipt_values = build_receipt_values(
        ReceiptAssembly(
            workspace=workspace,
            skill_version=skill_version,
            skill_version_source=skill_version_source,
            skill_version_finished=version_finished,
            harness=arguments.harness,
            execution_level=arguments.execution_level,
            intent=arguments.intent,
            started_at=started_at,
            finished_at=utc_now(),
            lifecycle_status=project.lifecycle_status,
            config_status=project.status,
            policy_status=project.policy_status,
            sources_status=project.sources_status,
            state_map_status=project.state_map_status,
            readme_policy=readme_policy,
            readme_policy_source=readme_policy_source,
            readme_policy_confirmed_by=readme_policy_confirmed_by,
            local=local,
            local_fingerprint_started=local_started.fingerprint,
            local_fingerprint_finished=local_finished_fingerprint,
            local_changed_during_check=local_changed,
            local_observed_at=local_observed_at,
            adapter_fingerprint_started=adapter_started,
            adapter_fingerprint_finished=adapter_finished,
            adapter_final_status=adapter_final_status,
            adapter_changed_during_check=adapter_changed,
            remote=remote,
            remote_query_confirmed_by=(arguments.remote_confirmed_by or "UNCONFIRMED"),
            remote_query_confirmed_source_id=(
                arguments.remote_confirmed_source_id or "UNCONFIRMED"
            ),
            remote_max_age_seconds=remote_max_age_seconds,
            remote_observed_at=remote_observed_at,
            runtime=runtime,
            runtime_candidates=runtime_candidates,
            runtime_max_age_seconds=runtime_max_age_seconds,
            runtime_observed_at=runtime_observed_at,
            capabilities=capabilities,
            capabilities_max_age_seconds=capabilities_max_age_seconds,
            capabilities_observed_at=capabilities_observed_at,
            state_verdict=verdict,
            read_gate=read_gate,
            write_gate=write_gate_value,
            target_status=target_status,
            target_fields=target_fields,
            human_decision=human_decision,
            decision_reason=decision_reason,
            collected_by=arguments.collected_by,
            synthesized_by=arguments.synthesized_by,
            decided_by=decided_by,
        )
    )
    receipt_path, _ = write_receipt(
        receipt_values,
        workspace=workspace,
        receipt_root=(Path(arguments.receipt_root) if arguments.receipt_root else None),
    )
    return {
        "LOCAL": local.result,
        "REMOTE": remote.result,
        "RUNTIME": runtime.result,
        "CAPABILITIES": capabilities.result,
        "STATE_VERDICT": verdict,
        "READ_GATE": read_gate,
        "WRITE_GATE": write_gate_value,
        "TARGET": target_status,
        "RECEIPT": display_path(receipt_path, workspace),
        "HUMAN_DECISION": human_decision,
        "DECISION_REASON": decision_reason,
    }


def _runtime_observation(
    arguments: argparse.Namespace,
    sources: dict[str, str],
    candidates: tuple[str, ...],
) -> RuntimeObservation:
    runtime = normalize_runtime(
        requested_result=arguments.runtime_result,
        version=arguments.runtime_version,
        target=arguments.runtime_target,
        source=arguments.runtime_source,
        evidence_level=arguments.runtime_evidence,
        configured_mode=sources.get("RUNTIME_MODE", "UNDECLARED").upper(),
    )
    if (
        arguments.runtime_result == "AUTO"
        and len(candidates) > 1
        and not arguments.runtime_source
    ):
        return RuntimeObservation(
            result="PARTIAL",
            state="MULTIPLE_CANDIDATES",
            version="UNKNOWN",
            target="UNKNOWN",
            source="SOURCES.env",
            evidence_level="DECLARED",
        )
    return runtime


def _finish_local(
    workspace: Path,
    local_started,
    *,
    timeout_seconds: int,
    max_entries: int,
):
    try:
        local_finished, _ = probe_local(
            workspace,
            timeout_seconds=timeout_seconds,
            max_entries=max_entries,
        )
        return local_finished, local_finished.fingerprint, True
    except (OSError, ValueError):
        return (
            replace(
                local_started,
                result="STALE",
                scan_status="FINAL_PROBE_UNAVAILABLE",
            ),
            "UNAVAILABLE",
            False,
        )


def _finish_version(source_root: Path | None, started_version: str) -> str:
    if source_root is None:
        return started_version
    try:
        return read_version(source_root)
    except (OSError, UnicodeError, ValueError):
        return "UNAVAILABLE"


def _finish_adapter(adapter_root: Path) -> tuple[str, str]:
    try:
        return adapter_fingerprint(adapter_root), "COMPLETE"
    except (OSError, ValueError):
        return "UNAVAILABLE", "UNAVAILABLE"


def _configured_limit(
    *,
    explicit: int,
    configured: str | None,
    default: int,
    maximum: int,
) -> int:
    configured_value = positive_int(
        configured,
        default=default,
        maximum=maximum,
    )
    return positive_int(
        str(explicit) if explicit else None,
        default=configured_value,
        maximum=maximum,
    )

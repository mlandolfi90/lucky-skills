from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from adopcion.models import AdoptionPlan
from adopcion.planner import build_plan as build_adoption_plan
from lifecycle_core.authorization import require_human
from lifecycle_core.envfile import load_env
from lifecycle_core.git import clone_repository, head
from lifecycle_core.manifest import Version, dependency_closure, validate_skill

from .branches import validate_branch_prefix
from .landing import create_landing_receipt
from .models import RepositoryAssessment, SyncPlan
from .registry import RepositoryEntry, load_registry


CLASSIFICATIONS = {"CURRENT", "READY_FAST", "NEEDS_ADAPTATION", "BLOCKED"}


def build_sync_plan(
    *,
    catalog: Path,
    registry: Path,
    skill_id: str,
    confirmed_by: str,
    branch_prefix: str = "codex/",
) -> SyncPlan:
    actor = require_human(confirmed_by, field="confirmed_by")
    normalized_branch_prefix = validate_branch_prefix(branch_prefix)
    catalog_root = catalog.resolve(strict=True)
    manifest = validate_skill(catalog_root / skill_id)
    dependency_closure(catalog_root, skill_id)
    assessments = tuple(
        _assess(
            entry,
            catalog_root=catalog_root,
            skill_id=skill_id,
            target_version=manifest.version,
            source_hash=manifest.content_hash,
            actor=actor,
        )
        for entry in load_registry(registry)
        if entry.includes(skill_id)
    )
    return SyncPlan(
        catalog=str(catalog_root),
        registry=str(registry.resolve(strict=True)),
        skill_id=skill_id,
        skill_version=str(manifest.version),
        branch_prefix=normalized_branch_prefix,
        source_hash=manifest.content_hash,
        repositories=assessments,
    ).with_hash()


def adoption_transition_hash(plan: AdoptionPlan) -> str:
    values = {
        "skill_id": plan.skill_id,
        "skill_version": plan.skill_version,
        "harness": plan.harness,
        "dependencies": plan.dependencies,
        "items": [
            {
                "skill_id": item.skill_id,
                "role": item.role,
                "destination": item.destination,
                "action": item.action,
                "source_hash": item.source_hash,
                "current_hash": item.current_hash,
            }
            for item in plan.items
        ],
        "collisions": plan.collisions,
        "risks": plan.risks,
    }
    canonical = json.dumps(
        values,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assess(
    entry: RepositoryEntry,
    *,
    catalog_root: Path,
    skill_id: str,
    target_version: Version,
    source_hash: str,
    actor: str,
) -> RepositoryAssessment:
    if entry.status == "PAUSED":
        return _blocked(entry, "REGISTRY_PAUSED")
    with tempfile.TemporaryDirectory(prefix=f"sync-scan-{entry.repo_id}-") as raw:
        temporary = Path(raw)
        clone = temporary / "repository"
        result = clone_repository(
            entry.remote_url,
            clone,
            branch=entry.default_branch,
        )
        if result.returncode != 0:
            return _blocked(entry, "REMOTE_INACCESSIBLE")
        remote_head = head(clone)
        classification, observed, reason = _classify_state(
            clone,
            entry,
            skill_id=skill_id,
            target_version=target_version,
            source_hash=source_hash,
        )
        if classification in {"CURRENT", "BLOCKED"}:
            return RepositoryAssessment(
                repo_id=entry.repo_id,
                remote_url=entry.remote_url,
                default_branch=entry.default_branch,
                harness=entry.harness,
                remote_head=remote_head,
                observed_version=observed,
                classification=classification,
                reason=reason,
                transition_hash="NONE",
                changes=(),
                risks=(),
                collisions=(),
            )
        try:
            landing = create_landing_receipt(
                workspace=clone,
                harness=entry.harness,
                confirmed_by=actor,
                receipt_root=temporary / "receipts",
            )
            adoption = build_adoption_plan(
                source_skill=catalog_root / skill_id,
                target=clone,
                harness=entry.harness,
                landing_receipt=landing,
            )
        except (OSError, ValueError):
            return RepositoryAssessment(
                repo_id=entry.repo_id,
                remote_url=entry.remote_url,
                default_branch=entry.default_branch,
                harness=entry.harness,
                remote_head=remote_head,
                observed_version=observed,
                classification="BLOCKED",
                reason="LANDING_OR_ADOPTION_BLOCKED",
                transition_hash="NONE",
                changes=(),
                risks=(),
                collisions=(),
            )
        return RepositoryAssessment(
            repo_id=entry.repo_id,
            remote_url=entry.remote_url,
            default_branch=entry.default_branch,
            harness=entry.harness,
            remote_head=remote_head,
            observed_version=observed,
            classification=classification,
            reason=reason,
            transition_hash=adoption_transition_hash(adoption),
            changes=tuple(
                f"{item.action}:{item.destination}"
                for item in adoption.items
                if item.action != "UNCHANGED"
            ),
            risks=adoption.risks,
            collisions=adoption.collisions,
        )


def _classify_state(
    clone: Path,
    entry: RepositoryEntry,
    *,
    skill_id: str,
    target_version: Version,
    source_hash: str,
) -> tuple[str, str, str]:
    state_path = clone / ".lifecycle" / "state" / "skills" / f"{skill_id}.env"
    if not state_path.exists():
        return "NEEDS_ADAPTATION", "NONE", "INITIAL_ADOPTION"
    try:
        values = load_env(state_path)
        if values.get("SKILL_ID") != skill_id or values.get("STATUS") != "ACTIVE":
            return "BLOCKED", "INVALID", "STATE_INVALID"
        observed = Version.parse(values["SKILL_VERSION"])
    except (OSError, KeyError, ValueError):
        return "BLOCKED", "INVALID", "STATE_INVALID"
    harnesses = set(values.get("HARNESSES", "").split(","))
    if observed == target_version:
        if values.get("CONTENT_HASH") == source_hash and entry.harness in harnesses:
            return "CURRENT", str(observed), "ALIGNED"
        return "NEEDS_ADAPTATION", str(observed), "CONTENT_OR_HARNESS_DRIFT"
    if observed > target_version:
        return "BLOCKED", str(observed), "TARGET_OLDER_THAN_REPOSITORY"
    if observed.major == target_version.major:
        return "READY_FAST", str(observed), "COMPATIBLE_UPGRADE"
    return "NEEDS_ADAPTATION", str(observed), "MAJOR_OR_INITIAL_ADAPTATION"


def _blocked(entry: RepositoryEntry, reason: str) -> RepositoryAssessment:
    return RepositoryAssessment(
        repo_id=entry.repo_id,
        remote_url=entry.remote_url,
        default_branch=entry.default_branch,
        harness=entry.harness,
        remote_head="UNKNOWN",
        observed_version="UNKNOWN",
        classification="BLOCKED",
        reason=reason,
        transition_hash="NONE",
        changes=(),
        risks=(),
        collisions=(),
    )

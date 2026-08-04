from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from adopcion.planner import build_plan as build_adoption_plan
from adopcion.transaction import apply_plan as apply_adoption_plan
from lifecycle_core.authorization import require_human
from lifecycle_core.envfile import canonical_env, load_env
from lifecycle_core.git import (
    all_dirty_paths,
    clone_repository,
    commit_paths,
    git,
    head,
)
from lifecycle_core.manifest import validate_skill
from lifecycle_core.receipts import operation_id, utc_now, write_receipt
from sextante.local_probe import probe_local

from .branches import release_branch
from .landing import create_landing_receipt
from .models import RepositoryAssessment, SyncPlan
from .scanner import APPLICABLE, adoption_transition_hash


@dataclass(frozen=True)
class SyncApplyResult:
    result: str
    receipts: tuple[Path, ...]


def apply_sync_plan(
    plan: SyncPlan,
    *,
    confirmed_plan_hash: str,
    selected_repositories: tuple[str, ...],
    confirmed_by: str,
    push_confirmed_by: str,
    git_author_name: str,
    git_author_email: str,
    accept_risks_by: str = "",
    accept_adaptation_by: str = "",
) -> SyncApplyResult:
    actor = require_human(confirmed_by, field="confirmed_by")
    require_human(push_confirmed_by, field="push_confirmed_by")
    if confirmed_plan_hash != plan.plan_hash or plan.plan_hash != plan.compute_hash():
        raise ValueError("la confirmación no coincide con BATCH_PLAN")
    selected = _selected(plan, selected_repositories)
    # `NEEDS_ADAPTATION` mezcla dos casos: la adopción inicial (aplicar está
    # bien: así entran repos nuevos) y el salto MAJOR o drift de contenido
    # (aplicar entrega una ruptura a un repo que aún no se adaptó). El segundo
    # exige aceptación humana explícita, como los riesgos.
    needs_acceptance = tuple(
        item.repo_id
        for item in selected
        if item.classification == "NEEDS_ADAPTATION"
        and item.reason != "INITIAL_ADOPTION"
    )
    if needs_acceptance:
        require_human(accept_adaptation_by, field="accept_adaptation_by")
    _safe_identity(git_author_name, "git_author_name")
    _safe_identity(git_author_email, "git_author_email")
    if any(item.risks for item in selected):
        require_human(accept_risks_by, field="accept_risks_by")
    catalog = Path(plan.catalog).resolve(strict=True)
    manifest = validate_skill(catalog / plan.skill_id)
    if (
        str(manifest.version) != plan.skill_version
        or manifest.content_hash != plan.source_hash
    ):
        raise ValueError("el catálogo cambió desde BATCH_PLAN")

    receipts: list[Path] = []
    completed = 0
    for assessment in selected:
        receipt = _apply_repository(
            plan,
            assessment,
            actor=actor,
            push_actor=push_confirmed_by,
            risk_actor=accept_risks_by,
            git_author_name=git_author_name,
            git_author_email=git_author_email,
        )
        receipts.append(receipt)
        values = load_env(receipt)
        if values["RESULT"] == "COMPLETE":
            completed += 1
    result = (
        "COMPLETE"
        if completed == len(selected)
        else ("BLOCKED" if completed == 0 else "PARTIAL")
    )
    return SyncApplyResult(result=result, receipts=tuple(receipts))


def _apply_repository(
    plan: SyncPlan,
    assessment: RepositoryAssessment,
    *,
    actor: str,
    push_actor: str,
    risk_actor: str,
    git_author_name: str,
    git_author_email: str,
) -> Path:
    result = "BLOCKED"
    reason = "UNKNOWN"
    commit = "NO"
    push = "NO"
    branch = release_branch(
        prefix=plan.branch_prefix,
        skill_id=plan.skill_id,
        skill_version=plan.skill_version,
        plan_hash=plan.plan_hash,
    )
    with tempfile.TemporaryDirectory(prefix=f"sync-apply-{assessment.repo_id}-") as raw:
        temporary = Path(raw)
        clone = temporary / "repository"
        cloned = clone_repository(
            assessment.remote_url,
            clone,
            branch=assessment.default_branch,
        )
        if cloned.returncode != 0:
            reason = "REMOTE_INACCESSIBLE"
        elif head(clone) != assessment.remote_head:
            reason = "REMOTE_CHANGED_SINCE_PLAN"
        else:
            try:
                landing = create_landing_receipt(
                    workspace=clone,
                    harness=assessment.harness,
                    confirmed_by=actor,
                    receipt_root=temporary / "receipts",
                )
                adoption = build_adoption_plan(
                    source_skill=Path(plan.catalog) / plan.skill_id,
                    target=clone,
                    harness=assessment.harness,
                    landing_receipt=landing,
                )
                if adoption_transition_hash(adoption) != assessment.transition_hash:
                    raise ValueError("ADOPTION_CHANGED_SINCE_PLAN")
                apply_adoption_plan(
                    adoption,
                    confirmed_plan_hash=adoption.plan_hash,
                    confirmed_by=actor,
                    accept_risk_by=risk_actor,
                )
                changed = all_dirty_paths(clone)
                _ensure_only_adoption_paths(changed, adoption)
                _git_ok(
                    clone,
                    ("config", "user.name", git_author_name),
                    "git config user.name",
                )
                _git_ok(
                    clone,
                    ("config", "user.email", git_author_email),
                    "git config user.email",
                )
                _git_ok(clone, ("checkout", "-b", branch), "git checkout")
                commit = commit_paths(
                    clone,
                    changed,
                    message=(
                        f"chore(skills): sync {plan.skill_id} " f"{plan.skill_version}"
                    ),
                )
                commit = _refresh_state_map_and_amend(clone)
                pushed = git(
                    clone,
                    ("push", "origin", f"HEAD:refs/heads/{branch}"),
                    timeout=120,
                )
                if pushed.returncode == 0:
                    push = "PUSHED"
                    result = "COMPLETE"
                    reason = "NONE"
                else:
                    push = "REJECTED"
                    result = "HUMAN_REQUIRED"
                    reason = "PUSH_REJECTED"
            except (OSError, ValueError) as error:
                reason = _single_line(str(error))

    receipt_root = Path(plan.catalog).parent / ".lifecycle" / "local" / "sync"
    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_id = operation_id("sync", f"{plan.plan_hash}:{assessment.repo_id}")
    return write_receipt(
        receipt_root / f"{receipt_id}.env",
        {
            "FORMAT_VERSION": "1",
            "SYNC_ID": receipt_id,
            "BATCH_PLAN": plan.plan_hash,
            "REPO_ID": assessment.repo_id,
            "REMOTE_HEAD": assessment.remote_head,
            "SKILL_ID": plan.skill_id,
            "SKILL_VERSION": plan.skill_version,
            "BRANCH": branch,
            "COMMIT": commit,
            "PUSH": push,
            "PR": "NOT_AVAILABLE",
            "RESULT": result,
            "REASON": reason,
            "CONFIRMED_BY": actor,
            "PUSH_CONFIRMED_BY": push_actor,
            "RISK_ACCEPTED_BY": risk_actor or "NOT_APPLICABLE",
            "GIT_AUTHOR_NAME": git_author_name,
            "GIT_AUTHOR_EMAIL": git_author_email,
            "FINISHED_AT": utc_now(),
        },
    )


def _selected(
    plan: SyncPlan,
    selected_repositories: tuple[str, ...],
) -> tuple[RepositoryAssessment, ...]:
    if not selected_repositories or len(set(selected_repositories)) != len(
        selected_repositories
    ):
        raise ValueError("la selección de repositorios es vacía o duplicada")
    by_id = {item.repo_id: item for item in plan.repositories}
    unknown = sorted(set(selected_repositories) - set(by_id))
    if unknown:
        raise ValueError(f"repositorios fuera de BATCH_PLAN: {','.join(unknown)}")
    selected = tuple(by_id[repo_id] for repo_id in selected_repositories)
    invalid = tuple(
        item.repo_id
        for item in selected
        if item.classification not in APPLICABLE
        or item.transition_hash == "NONE"
    )
    if invalid:
        raise ValueError(f"repositorios no aplicables: {','.join(invalid)}")
    return selected


def _ensure_only_adoption_paths(
    changed: tuple[str, ...],
    adoption,
) -> None:
    allowed = tuple(
        item.destination.rstrip("/")
        for item in adoption.items
        if item.action != "UNCHANGED"
    ) + (f".lifecycle/archive/{adoption.adoption_id}",)
    unexpected = tuple(
        path
        for path in changed
        if not any(
            path == prefix or path.startswith(f"{prefix}/") for prefix in allowed
        )
    )
    if unexpected:
        raise ValueError("Adopción tocó rutas fuera del plan: " + ",".join(unexpected))


def _refresh_state_map_and_amend(workspace: Path) -> str:
    state_map = workspace / ".lifecycle" / "state" / "STATE-MAP.env"
    if not state_map.is_file():
        return head(workspace)
    observation, _ = probe_local(
        workspace,
        timeout_seconds=10,
        max_entries=50_000,
    )
    values = load_env(state_map)
    values["GIT_LOCAL_FINGERPRINT"] = observation.fingerprint
    temporary = state_map.with_suffix(".env.tmp")
    temporary.write_text(
        canonical_env(values),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, state_map)
    corroborated, _ = probe_local(
        workspace,
        timeout_seconds=10,
        max_entries=50_000,
    )
    if corroborated.fingerprint != observation.fingerprint:
        raise ValueError("STATE-MAP no estabilizó después del commit")
    _git_ok(
        workspace,
        ("add", "--", ".lifecycle/state/STATE-MAP.env"),
        "git add STATE-MAP",
    )
    _git_ok(workspace, ("commit", "--amend", "--no-edit"), "git commit --amend")
    final, _ = probe_local(
        workspace,
        timeout_seconds=10,
        max_entries=50_000,
    )
    status_paths = all_dirty_paths(workspace)
    if final.fingerprint != observation.fingerprint or status_paths:
        raise ValueError(
            "STATE-MAP no coincide con el commit final:"
            f" expected={observation.fingerprint}"
            f" observed={final.fingerprint}"
            f" paths={','.join(status_paths)}"
        )
    return head(workspace)


def _git_ok(workspace: Path, arguments: tuple[str, ...], action: str) -> None:
    result = git(workspace, arguments, timeout=60)
    if result.returncode != 0:
        raise ValueError(f"{action} falló: {_single_line(result.stderr)}")


def _safe_identity(value: str, field: str) -> None:
    if not value.strip() or any(character in value for character in "\r\n\0"):
        raise ValueError(f"{field} inválido")


def _single_line(value: str) -> str:
    normalized = " ".join(value.split())
    return normalized[:240] or "UNKNOWN"

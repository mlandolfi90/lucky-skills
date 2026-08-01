from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

from lifecycle_core.authorization import require_human
from lifecycle_core.envfile import canonical_env, load_env
from lifecycle_core.git import commit_paths, git, is_repository
from lifecycle_core.hashing import sha256_file, tree_hash
from lifecycle_core.locking import directory_lock
from lifecycle_core.paths import resolve_within
from lifecycle_core.receipts import local_state_root, utc_now, write_receipt
from sextante.local_probe import probe_local

from .models import AdoptionPlan
from .planner import build_plan


def apply_plan(
    plan: AdoptionPlan,
    *,
    confirmed_plan_hash: str,
    confirmed_by: str,
    accept_risk_by: str = "",
    create_commit: bool = False,
    commit_confirmed_by: str = "",
) -> Path:
    actor = require_human(confirmed_by, field="confirmed_by")
    if confirmed_plan_hash != plan.plan_hash:
        raise ValueError("la confirmación no coincide con PLAN_HASH")
    if any(item.action == "BLOCK" for item in plan.items):
        raise ValueError("el plan contiene rutas bloqueadas")
    if plan.risks:
        require_human(accept_risk_by, field="accept_risk_by")
    if create_commit:
        require_human(commit_confirmed_by, field="commit_confirmed_by")

    target = Path(plan.target).resolve(strict=True)
    if create_commit and not is_repository(target):
        raise ValueError("se autorizó commit pero TARGET no usa Git")
    lifecycle = target / ".lifecycle"
    lifecycle_existed = lifecycle.exists()
    _require_current_plan(plan)
    lock = _lock_path(target, lifecycle_existed=lifecycle_existed)
    lock.parent.mkdir(parents=True, exist_ok=True)
    owner: dict[str, object] = {
        "ADOPTION_ID": plan.adoption_id,
        "PLAN_HASH": plan.plan_hash,
        "OWNER": actor,
        "CREATED_AT": utc_now(),
    }
    changed_paths: set[str] = set()
    created_archive_roots: list[Path] = []
    receipt_path = lifecycle / "local" / "adopcion" / f"{plan.adoption_id}.env"
    receipt_existed = receipt_path.exists()

    with directory_lock(lock, owner):
        _require_current_plan(plan)
        with tempfile.TemporaryDirectory(
            prefix=f".{plan.adoption_id}-",
            dir=target.parent,
        ) as temporary:
            scratch = Path(temporary)
            staged = scratch / "staged"
            backup = scratch / "backup"
            archive = scratch / "archive"
            _prepare(plan, staged)
            _backup(plan, target, backup, archive)
            try:
                _activate(plan, target, staged, changed_paths)
                state_paths = _write_states(plan, target, actor)
                changed_paths.update(state_paths)
                archive_paths = _install_archive(
                    plan,
                    target,
                    archive,
                    actor,
                    created_archive_roots,
                )
                changed_paths.update(archive_paths)
                state_map_paths = _write_state_map(plan, target)
                changed_paths.update(state_map_paths)
                _validate_activation(plan, target)
                vcs_visible, vcs_ignored = _vcs_visibility(target, changed_paths)
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                write_receipt(
                    receipt_path,
                    {
                        "FORMAT_VERSION": "1",
                        "ADOPTION_ID": plan.adoption_id,
                        "PLAN_HASH": plan.plan_hash,
                        "SKILL_ID": plan.skill_id,
                        "SKILL_VERSION": plan.skill_version,
                        "TARGET": str(target),
                        "HARNESS": plan.harness,
                        "RESULT": ("ADOPTED" if plan.has_writes else "ALREADY_ADOPTED"),
                        "COLLISIONS": ",".join(plan.collisions) or "NONE",
                        "RISKS": ",".join(plan.risks) or "NONE",
                        "CONFIRMED_BY": actor,
                        "COMMIT_CONFIRMED_BY": (
                            commit_confirmed_by if create_commit else "NOT_APPLICABLE"
                        ),
                        "APPLIED_AT": utc_now(),
                        "VCS_VISIBLE": vcs_visible,
                        "VCS_IGNORED": vcs_ignored,
                        "COMMIT": "REQUESTED" if create_commit else "NO",
                    },
                )
            except Exception as error:
                _restore(plan, target, backup)
                _remove_created_archives(created_archive_roots, target)
                if not receipt_existed and receipt_path.exists():
                    receipt_path.unlink()
                _prune_empty_parents(receipt_path.parent, target)
                # Nota PEP 678: confirma el rollback sin alterar el tipo ni el
                # mensaje original de la excepción. El CLI la muestra aparte.
                error.add_note(
                    "ROLLBACK=RESTORED: el TARGET volvió al estado previo a la "
                    "adopción"
                )
                raise

    if create_commit:
        commit = commit_paths(
            target,
            sorted(changed_paths),
            message=f"chore(skills): adopt {plan.skill_id} {plan.skill_version}",
        )
        _append_commit_result(receipt_path, commit, commit_confirmed_by)
    return receipt_path


def _vcs_visibility(target: Path, changed_paths: set[str]) -> tuple[str, str]:
    """Declarar qué parte de lo escrito es visible para git.

    Un .gitignore del proyecto (p. ej. `*.env` en un repo de auth) puede
    tragarse los metadatos de gobernanza en silencio: la adopción reportaba
    ADOPTED y otro clon o el CI no veían nada. El choque es legítimo de ambos
    lados; lo que no es legítimo es callarlo. Hallado en vivo adoptando
    Lucky-Auth-Plane.
    """
    if not changed_paths:
        return "0/0", "NONE"
    if not is_repository(target):
        return "NOT_APPLICABLE", "NOT_APPLICABLE"
    ordered = sorted(changed_paths)
    result = git(target, ("check-ignore", "--", *ordered))
    ignored = tuple(
        line.strip() for line in result.stdout.splitlines() if line.strip()
    )
    visible = len(ordered) - len(ignored)
    return f"{visible}/{len(ordered)}", ",".join(ignored) or "NONE"


def _prepare(plan: AdoptionPlan, staged: Path) -> None:
    for item in plan.items:
        if item.action not in {"CREATE", "ARCHIVE_REPLACE"}:
            continue
        if item.role in {"STATE", "STATE_MAP"}:
            continue
        destination = staged / Path(item.destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if item.role in {"LIFECYCLE_IGNORE", "LIFECYCLE_ATTRIBUTES"}:
            content = (
                "local/\n"
                if item.role == "LIFECYCLE_IGNORE"
                else "* text=auto eol=lf\n"
            )
            destination.write_text(content, encoding="utf-8", newline="\n")
            continue
        source = Path(item.source)
        shutil.copytree(source, destination)


def _backup(plan: AdoptionPlan, target: Path, backup: Path, archive: Path) -> None:
    for item in plan.items:
        if item.action not in {"ARCHIVE_REPLACE", "ARCHIVE_REMOVE"}:
            continue
        source = resolve_within(target, item.destination)
        backup_target = backup / Path(item.destination)
        archive_target = archive / "files" / Path(item.destination)
        _copy_path(source, backup_target)
        _copy_path(source, archive_target)


def _activate(
    plan: AdoptionPlan,
    target: Path,
    staged: Path,
    changed_paths: set[str],
) -> None:
    for item in plan.items:
        if item.action == "UNCHANGED":
            continue
        if item.role in {"STATE", "STATE_MAP"}:
            continue
        destination = resolve_within(target, item.destination)
        if destination.exists():
            _remove_path(destination)
        if item.action != "ARCHIVE_REMOVE":
            prepared = staged / Path(item.destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_path(prepared, destination)
        changed_paths.add(item.destination)


def _write_states(
    plan: AdoptionPlan,
    target: Path,
    actor: str,
) -> tuple[str, ...]:
    state_root = target / ".lifecycle" / "state" / "skills"
    state_root.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for dependency in plan.dependencies:
        skill_id, _, version = dependency.partition("@")
        state_item = next(
            item
            for item in plan.items
            if item.skill_id == skill_id and item.role == "STATE"
        )
        if state_item.action == "UNCHANGED":
            continue
        source = next(
            item
            for item in plan.items
            if item.skill_id == skill_id and item.role == "CANONICAL"
        )
        values = {
            "FORMAT_VERSION": "1",
            "SKILL_ID": skill_id,
            "SKILL_VERSION": version,
            # Forma canónica portable; debe coincidir con la que el planner
            # incluyó en el hash esperado del estado.
            "SOURCE": f"skills/{skill_id}",
            "SOURCE_COMMIT": "N/D",
            "HARNESSES": plan.harness,
            "STATUS": "ACTIVE",
            "ADOPTION_ID": plan.adoption_id,
            "ADOPTED_BY": actor,
            "ADOPTED_AT": utc_now(),
            "CONTENT_HASH": source.source_hash,
        }
        state_path = state_root / f"{skill_id}.env"
        temporary = state_path.with_suffix(".env.tmp")
        temporary.write_text(
            canonical_env(values),
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, state_path)
        paths.append(state_path.relative_to(target).as_posix())
    return tuple(paths)


def _write_state_map(plan: AdoptionPlan, target: Path) -> tuple[str, ...]:
    item = next(item for item in plan.items if item.role == "STATE_MAP")
    if item.action == "UNCHANGED":
        return ()
    state_map = resolve_within(target, item.destination)
    state_map.parent.mkdir(parents=True, exist_ok=True)
    before, _ = probe_local(target, timeout_seconds=10, max_entries=50_000)
    initial = {
        "STATE_SCHEMA": "1",
        "STATE_REVISION": "1",
        "GIT_LOCAL_COMMIT": before.head,
        "GIT_LOCAL_FINGERPRINT": "UNKNOWN",
        "GIT_REMOTE_COMMIT": "UNKNOWN",
        "GIT_REMOTE_REF": "UNKNOWN",
        "RUNTIME_VERSION": "UNKNOWN",
        "CAPABILITIES_HASH": "UNKNOWN",
        "TARGET_WHERE": "UNCONFIRMED",
        "TARGET_ACTION": "UNCONFIRMED",
        "TARGET_CONFIRMED_BY": "UNCONFIRMED",
    }
    _replace_env(state_map, initial)
    observation, _ = probe_local(target, timeout_seconds=10, max_entries=50_000)
    initial["GIT_LOCAL_FINGERPRINT"] = observation.fingerprint
    _replace_env(state_map, initial)
    corroborated, _ = probe_local(target, timeout_seconds=10, max_entries=50_000)
    if corroborated.fingerprint != observation.fingerprint:
        raise ValueError("STATE-MAP no produjo una huella estable")
    return (item.destination,)


def _install_archive(
    plan: AdoptionPlan,
    target: Path,
    archive: Path,
    actor: str,
    created_roots: list[Path],
) -> tuple[str, ...]:
    archived_items = tuple(
        item
        for item in plan.items
        if item.action in {"ARCHIVE_REPLACE", "ARCHIVE_REMOVE"}
    )
    if not archived_items:
        return ()
    archive_target = target / ".lifecycle" / "archive" / plan.adoption_id
    if archive_target.exists():
        raise ValueError("el archivo de esta adopción ya existe")
    archive_target.parent.mkdir(parents=True, exist_ok=True)
    payload_location = "VERSIONED"
    if plan.risks:
        payload_target = (
            target / ".lifecycle" / "local" / "archive" / plan.adoption_id / "files"
        )
        if payload_target.exists():
            raise ValueError("el archivo local de esta adopción ya existe")
        local_adoption_root = payload_target.parent
        created_roots.append(
            payload_target if local_adoption_root.exists() else local_adoption_root
        )
        created_roots.append(archive_target)
        payload_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(archive / "files", payload_target)
        archive_target.mkdir(parents=True)
        payload_location = (
            Path(".lifecycle") / "local" / "archive" / plan.adoption_id / "files"
        ).as_posix()
    else:
        created_roots.append(archive_target)
        shutil.copytree(archive, archive_target)
    manifest = {
        "FORMAT_VERSION": "1",
        "ADOPTION_ID": plan.adoption_id,
        "PLAN_HASH": plan.plan_hash,
        # El manifiesto vive dentro del propio TARGET y se versiona; una ruta
        # absoluta filtraría la máquina de quien adoptó sin agregar información.
        "TARGET": ".",
        "ARCHIVED_PATHS": ",".join(item.destination for item in archived_items),
        "PAYLOAD_LOCATION": payload_location,
        "ARCHIVED_BY": actor,
        "ARCHIVED_AT": utc_now(),
    }
    (archive_target / "MANIFEST.env").write_text(
        canonical_env(manifest),
        encoding="utf-8",
        newline="\n",
    )
    return (archive_target.relative_to(target).as_posix(),)


def _validate_activation(plan: AdoptionPlan, target: Path) -> None:
    for item in plan.items:
        destination = resolve_within(target, item.destination)
        if item.action == "ARCHIVE_REMOVE":
            if destination.exists():
                raise ValueError(f"{item.destination}: no fue removido")
            continue
        if item.role == "STATE_MAP":
            values = load_env(destination)
            observation, _ = probe_local(
                target,
                timeout_seconds=10,
                max_entries=50_000,
            )
            if values.get("GIT_LOCAL_FINGERPRINT") != observation.fingerprint:
                raise ValueError("STATE-MAP no coincide con el TARGET")
            continue
        if item.role == "STATE":
            values = load_env(destination)
            observed = {
                "SKILL_ID": values.get("SKILL_ID", ""),
                "SKILL_VERSION": values.get("SKILL_VERSION", ""),
                "SOURCE": values.get("SOURCE", ""),
                "HARNESSES": values.get("HARNESSES", ""),
                "STATUS": values.get("STATUS", ""),
                "CONTENT_HASH": values.get("CONTENT_HASH", ""),
            }
            observed_hash = hashlib.sha256(
                canonical_env(observed).encode("utf-8")
            ).hexdigest()
            if observed_hash != item.source_hash:
                raise ValueError(f"{item.destination}: estado instalado inválido")
            continue
        if item.role in {"LIFECYCLE_IGNORE", "LIFECYCLE_ATTRIBUTES"}:
            if sha256_file(destination) != item.source_hash:
                raise ValueError(f"{item.destination}: regla lifecycle no canónica")
            continue
        if tree_hash(destination) != item.source_hash:
            raise ValueError(f"{item.destination}: huella instalada inválida")


def _restore(plan: AdoptionPlan, target: Path, backup: Path) -> None:
    for item in reversed(plan.items):
        if item.action == "UNCHANGED":
            continue
        destination = resolve_within(target, item.destination)
        if destination.exists():
            _remove_path(destination)
            _prune_empty_parents(destination.parent, target)
        saved = backup / Path(item.destination)
        if saved.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_path(saved, destination)


def _copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _append_commit_result(receipt_path: Path, commit: str, confirmed_by: str) -> None:
    write_receipt(
        receipt_path.with_name(f"{receipt_path.stem}-commit.env"),
        {
            "FORMAT_VERSION": "1",
            "ADOPTION_RECEIPT": str(receipt_path),
            "COMMIT": commit,
            "COMMIT_CONFIRMED_BY": confirmed_by,
            "RECORDED_AT": utc_now(),
        },
    )


def _replace_env(path: Path, values: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        canonical_env(values),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _prune_empty_parents(path: Path, root: Path) -> None:
    current = path
    while current != root and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _remove_created_archives(created_roots: list[Path], target: Path) -> None:
    for created_root in reversed(created_roots):
        if created_root.exists():
            shutil.rmtree(created_root)
        _prune_empty_parents(created_root.parent, target)


def _require_current_plan(plan: AdoptionPlan) -> None:
    current = build_plan(
        source_skill=Path(plan.source_skill),
        target=Path(plan.target),
        harness=plan.harness,
        landing_receipt=Path(plan.landing_receipt),
        legacy_paths=tuple(
            item.destination for item in plan.items if item.role == "LEGACY"
        ),
    )
    if current.plan_hash != plan.plan_hash:
        raise ValueError("el estado cambió; recalcular y reconfirmar el plan")


def _lock_path(target: Path, *, lifecycle_existed: bool) -> Path:
    if lifecycle_existed:
        return target / ".lifecycle" / "local" / "locks" / "adopcion"
    workspace_id = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:16]
    lock_root = local_state_root("locks").resolve()
    if _is_within(lock_root, target):
        lock_root = (Path(tempfile.gettempdir()) / "skills-v3" / "locks").resolve()
    if _is_within(lock_root, target):
        raise ValueError("no existe un directorio de lock externo al TARGET")
    return lock_root / workspace_id / "adopcion"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

from lifecycle_core.authorization import require_human
from lifecycle_core.envfile import canonical_env, load_env
from lifecycle_core.git import commit_paths, git, is_repository
from lifecycle_core.hashing import sha256_bytes, sha256_file, tree_hash
from lifecycle_core.manifest import Version, dependency_closure, validate_skill
from lifecycle_core.receipts import operation_id, utc_now, verify_receipt, write_receipt
from skill_packaging.packager import SUPPORTED_HARNESSES, package_skills

from .models import ReleasePlan


REMOTE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


def build_release_plan(
    *,
    catalog: Path,
    skill_id: str,
    impact: str,
    closure_receipt: Path,
) -> ReleasePlan:
    catalog_root = catalog.resolve(strict=True)
    manifest = validate_skill(catalog_root / skill_id)
    dependency_closure(catalog_root, skill_id)
    closure_path = closure_receipt.resolve(strict=True)
    if not verify_receipt(closure_path):
        raise ValueError("el cierre no tiene un comprobante íntegro")
    closure = load_env(closure_path)
    required = {
        "KIND": "CLOSURE",
        "CLOSURE": "FINAL",
        "TESTS": "PASS",
    }
    for key, expected in required.items():
        if closure.get(key) != expected:
            raise ValueError(f"el cierre no habilita publicación: {key}")
    closure_hash = sha256_file(closure_path)
    repository = catalog_root.parent
    _require_unconsumed_closure(repository, closure_hash)
    _require_content_change(catalog_root, manifest)
    if _sin_tag_previo(catalog_root, manifest):
        # NACIMIENTO: una skill que nunca se publicó no se bumpea, se SELLA en
        # la versión que declara. Bumpear aquí publicaba 1.0.1 como primera
        # versión y llamaba PATCH ("corrección compatible") a un nacimiento —
        # una mentira sobre un contrato que nadie había publicado todavía. Las
        # 28 originales no lo destaparon porque las selló la migración, no
        # este ciclo; apareció al nacer la primera skill de verdad.
        normalized_impact = "INITIAL"
        to_version = manifest.version
    else:
        normalized_impact = impact.upper()
        if normalized_impact == "AUTO":
            # El bump se calcula, no se tipea: los commits convencionales desde
            # el último tag proponen el impacto. La autoridad humana no se
            # pierde — el impacto resuelto queda dentro del PLAN_HASH que se
            # confirma.
            normalized_impact = _propose_impact(catalog_root, manifest)
        to_version = manifest.version.bump(normalized_impact)
    return ReleasePlan(
        catalog=str(catalog_root),
        skill_id=manifest.skill_id,
        from_version=str(manifest.version),
        to_version=str(to_version),
        impact=normalized_impact,
        source_hash=tree_hash(manifest.root),
        closure_receipt=str(closure_path),
        closure_hash=closure_hash,
        canary_hash=_canary_hash(
            catalog_root,
            skill_id,
            override_version=str(to_version),
        ),
        # QUALITY no es una medición nueva: refleja el TESTS=PASS del cierre
        # consumido, verificado por el gate de arriba. Se deriva del recibo
        # (no un literal) para que la procedencia quede trazable; los
        # termómetros de conducta viven en evals/, fuera de este plan.
        quality=closure["TESTS"],
    ).with_hash()


def apply_release(
    plan: ReleasePlan,
    *,
    confirmed_plan_hash: str,
    confirmed_by: str,
    create_commit: bool = False,
    commit_confirmed_by: str = "",
    create_tag: bool = False,
    tag_confirmed_by: str = "",
    push: bool = False,
    push_confirmed_by: str = "",
    remote: str = "origin",
) -> Path:
    actor = require_human(confirmed_by, field="confirmed_by")
    if confirmed_plan_hash != plan.plan_hash:
        raise ValueError("la confirmación no coincide con PLAN_HASH")
    if plan.quality != "PASS":
        raise ValueError("QUALITY no habilita publicación")
    if create_commit:
        require_human(commit_confirmed_by, field="commit_confirmed_by")
    if create_tag:
        require_human(tag_confirmed_by, field="tag_confirmed_by")
        if not create_commit:
            raise ValueError("crear tag exige crear el commit de release")
    if push:
        require_human(push_confirmed_by, field="push_confirmed_by")
        if not create_commit:
            raise ValueError("push exige crear el commit de release")
        _validate_remote_name(remote)

    catalog = Path(plan.catalog).resolve(strict=True)
    skill_root = catalog / plan.skill_id
    manifest_path = skill_root / "manifest.env"
    repository = catalog.parent
    if create_commit and not is_repository(repository):
        raise ValueError("se autorizó commit pero el catálogo no usa Git")
    _revalidate_plan(plan, skill_root)
    _require_unconsumed_closure(repository, plan.closure_hash)
    original = manifest_path.read_bytes()
    manifest_values = load_env(manifest_path)
    manifest_values["SKILL_VERSION"] = plan.to_version
    temporary = manifest_path.with_suffix(".env.tmp")
    temporary.write_text(
        canonical_env(manifest_values),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, manifest_path)

    commit = "NO"
    tag = "NO"
    push_result = "NO"
    release_result = "READY"
    reason = "NONE"
    changelog_path = repository / "CHANGELOG.md"
    changelog_original = (
        changelog_path.read_bytes() if changelog_path.exists() else None
    )
    try:
        published = validate_skill(skill_root)
        if str(published.version) != plan.to_version:
            raise ValueError("la versión publicada no coincide")
        if _canary_hash(catalog, plan.skill_id) != plan.canary_hash:
            raise ValueError("el canary publicado no coincide con el plan")
        if create_commit:
            # Historia narrativa generada por la máquina, jamás mantenida a
            # mano: cada release deja su entrada en el CHANGELOG dentro del
            # mismo commit de release.
            _prepend_changelog(changelog_path, plan, actor)
            relative_skill = skill_root.relative_to(repository).as_posix()
            commit = commit_paths(
                repository,
                (relative_skill, "CHANGELOG.md"),
                message=f"chore(skills): release {plan.skill_id} {plan.to_version}",
            )
            release_result = "PUBLISHED"
        if create_tag:
            tag_name = _tag_name(plan)
            # Tag ANOTADO: un tag liviano es mutable sin dejar rastro; el
            # anotado lleva autor, fecha y mensaje. El ancla inmutable real
            # sigue siendo el commit que registra el recibo.
            result = git(
                repository,
                (
                    "tag",
                    "-a",
                    tag_name,
                    "-m",
                    f"release {plan.skill_id} {plan.to_version}",
                    commit,
                ),
            )
            if result.returncode != 0:
                tag = "REJECTED"
                release_result = "HUMAN_REQUIRED"
                reason = "TAG_REJECTED"
            else:
                tag = tag_name
        if push and tag != "REJECTED":
            branch_result = git(repository, ("branch", "--show-current"))
            branch = branch_result.stdout.strip()
            if branch_result.returncode != 0 or not branch:
                push_result = "NOT_ATTEMPTED"
                release_result = "HUMAN_REQUIRED"
                reason = "LOCAL_BRANCH_UNKNOWN"
            arguments = [
                "push",
                "--atomic",
                remote,
                f"{commit}:refs/heads/{branch}",
            ]
            if tag != "NO":
                arguments.append(f"refs/tags/{tag}")
            if push_result != "NOT_ATTEMPTED":
                result = git(repository, arguments, timeout=60)
                if result.returncode == 0:
                    push_result = "PUSHED"
                else:
                    push_result = "REJECTED"
                    release_result = "HUMAN_REQUIRED"
                    reason = "PUSH_REJECTED"
        elif push:
            push_result = "NOT_ATTEMPTED"
    except Exception:
        if commit == "NO":
            manifest_path.write_bytes(original)
            if changelog_original is not None:
                changelog_path.write_bytes(changelog_original)
            elif changelog_path.exists():
                changelog_path.unlink()
        raise

    receipt_root = repository / ".lifecycle" / "local" / "releases"
    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_id = operation_id("release", plan.plan_hash)
    receipt = write_receipt(
        receipt_root / f"{receipt_id}.env",
        {
            "FORMAT_VERSION": "1",
            "RELEASE_ID": receipt_id,
            "SKILL_ID": plan.skill_id,
            "FROM_VERSION": plan.from_version,
            "TO_VERSION": plan.to_version,
            "IMPACT": plan.impact,
            "PLAN_HASH": plan.plan_hash,
            "QUALITY": plan.quality,
            "CANARY_HASH": plan.canary_hash,
            "COMMIT": commit,
            "TAG": tag,
            "PUSH": push_result,
            "RELEASE": release_result,
            "REASON": reason,
            "CONFIRMED_BY": actor,
            "COMMIT_CONFIRMED_BY": (
                commit_confirmed_by if create_commit else "NOT_APPLICABLE"
            ),
            "TAG_CONFIRMED_BY": (tag_confirmed_by if create_tag else "NOT_APPLICABLE"),
            "PUSH_CONFIRMED_BY": (push_confirmed_by if push else "NOT_APPLICABLE"),
            "PUBLISHED_AT": utc_now(),
        },
    )
    _consume_closure(repository, plan, receipt_id)
    return receipt


def _prepend_changelog(path: Path, plan: ReleasePlan, actor: str) -> None:
    header = (
        "# Changelog de la suite\n\n"
        "Generado por publicar-skill; no editar a mano.\n"
    )
    body = path.read_text(encoding="utf-8") if path.exists() else header
    entry = (
        f"\n## {plan.skill_id} {plan.to_version} — {utc_now()[:10]}"
        f" — {plan.impact}\n"
        f"- {plan.from_version} → {plan.to_version} · QUALITY={plan.quality}"
        f" · autorizó {actor}\n"
    )
    rest = body[len(header):] if body.startswith(header) else body
    path.write_text(header + entry + rest, encoding="utf-8", newline="\n")


def _consumed_closure_marker(repository: Path, closure_hash: str) -> Path:
    return (
        repository
        / ".lifecycle"
        / "local"
        / "releases"
        / "consumed"
        / f"{closure_hash}.env"
    )


def _require_unconsumed_closure(repository: Path, closure_hash: str) -> None:
    # Un cierre autoriza exactamente una release. Sin este consumo, un cierre
    # viejo publicaba cualquier cosa, indefinidamente.
    marker = _consumed_closure_marker(repository, closure_hash)
    if marker.exists():
        values = load_env(marker)
        raise ValueError(
            "el cierre ya fue consumido por "
            f"{values.get('RELEASE_ID', 'otra release')}"
        )


def _consume_closure(repository: Path, plan: ReleasePlan, release_id: str) -> None:
    marker = _consumed_closure_marker(repository, plan.closure_hash)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        canonical_env(
            {
                "FORMAT_VERSION": "1",
                "CLOSURE_HASH": plan.closure_hash,
                "RELEASE_ID": release_id,
                "SKILL_ID": plan.skill_id,
                "TO_VERSION": plan.to_version,
                "CONSUMED_AT": utc_now(),
            }
        ),
        encoding="utf-8",
        newline="\n",
    )


def _sin_tag_previo(catalog_root: Path, manifest) -> bool:
    """¿La skill nunca se publicó? (no existe el tag de su versión vigente).

    Fuera de un repositorio no hay historia que consultar: se trata como
    publicada para no convertir cualquier checkout suelto en un nacimiento.
    """
    repository = catalog_root.parent
    if not is_repository(repository):
        return False
    tag_name = f"skill-{manifest.skill_id}-v{manifest.version}"
    tag_check = git(
        repository,
        ("rev-parse", "--verify", "--quiet", f"refs/tags/{tag_name}"),
    )
    return tag_check.returncode != 0


def _propose_impact(catalog_root: Path, manifest) -> str:
    """Proponer el impacto desde los commits convencionales de la skill.

    `BREAKING`/`!` → MAJOR; `feat` → MINOR; resto → PATCH. Sin repositorio o
    sin tag previo no hay historia comparable: PATCH, el impacto mínimo.
    """
    repository = catalog_root.parent
    if not is_repository(repository):
        return "PATCH"
    tag_name = f"skill-{manifest.skill_id}-v{manifest.version}"
    tag_check = git(
        repository,
        ("rev-parse", "--verify", "--quiet", f"refs/tags/{tag_name}"),
    )
    if tag_check.returncode != 0:
        return "PATCH"
    try:
        relative = manifest.root.relative_to(repository).as_posix()
    except ValueError:
        return "PATCH"
    log = git(
        repository,
        ("log", "--format=%s", f"{tag_name}..HEAD", "--", relative),
    )
    if log.returncode != 0:
        return "PATCH"
    subjects = [line.strip() for line in log.stdout.splitlines() if line.strip()]
    impact = "PATCH"
    for subject in subjects:
        head = subject.split(":", 1)[0]
        if "BREAKING" in subject or head.endswith("!"):
            return "MAJOR"
        if head.startswith("feat"):
            impact = "MINOR"
    return impact


def _require_content_change(catalog_root: Path, manifest) -> None:
    # Una release sin ningún cambio de contenido solo mueve el número de
    # versión: prohibida. Se compara el árbol actual de la skill contra el tag
    # de su versión vigente; sin tag previo (primera release) no hay contra qué
    # comparar y se permite.
    repository = catalog_root.parent
    if not is_repository(repository):
        return
    if _sin_tag_previo(catalog_root, manifest):
        return
    tag_name = f"skill-{manifest.skill_id}-v{manifest.version}"
    try:
        relative = manifest.root.relative_to(repository).as_posix()
    except ValueError:
        return
    diff = git(repository, ("diff", "--quiet", tag_name, "--", relative))
    if diff.returncode == 0:
        raise ValueError(
            f"sin cambios de contenido desde {manifest.version}; nada que publicar"
        )


def _revalidate_plan(plan: ReleasePlan, skill_root: Path) -> None:
    if plan.plan_hash != plan.compute_hash():
        raise ValueError("PLAN_HASH inválido")
    manifest = validate_skill(skill_root)
    if str(manifest.version) != plan.from_version:
        raise ValueError("la versión cambió desde el plan")
    if tree_hash(skill_root) != plan.source_hash:
        raise ValueError("la skill cambió desde el plan")
    closure = Path(plan.closure_receipt)
    if not verify_receipt(closure) or sha256_file(closure) != plan.closure_hash:
        raise ValueError("el comprobante de cierre cambió")
    esperada = (
        manifest.version
        if plan.impact == "INITIAL"
        else manifest.version.bump(plan.impact)
    )
    if esperada != Version.parse(plan.to_version):
        raise ValueError("la transición SemVer cambió")
    if (
        _canary_hash(
            Path(plan.catalog),
            plan.skill_id,
            override_version=plan.to_version,
        )
        != plan.canary_hash
    ):
        raise ValueError("el canary cambió desde el plan")


def _tag_name(plan: ReleasePlan) -> str:
    return f"skill-{plan.skill_id}-v{plan.to_version}"


def _canary_hash(
    catalog: Path,
    skill_id: str,
    *,
    override_version: str = "",
) -> str:
    repository = catalog.parent
    records: list[str] = []
    with tempfile.TemporaryDirectory(prefix=f"release-canary-{skill_id}-") as raw:
        temporary = Path(raw)
        if override_version:
            repository, catalog = _staged_catalog(
                repository,
                catalog,
                temporary,
                skill_id=skill_id,
                version=override_version,
            )
        output = temporary / "output"
        for harness in SUPPORTED_HARNESSES:
            result = package_skills(
                repository_root=repository,
                catalog_root=catalog,
                output_root=output / harness,
                skill_ids=(skill_id,),
                harness_id=harness,
            )
            records.append(f"{harness}:{result.content_hash}")
    return sha256_bytes(("\n".join(records) + "\n").encode("utf-8"))


def _staged_catalog(
    repository: Path,
    catalog: Path,
    temporary: Path,
    *,
    skill_id: str,
    version: str,
) -> tuple[Path, Path]:
    staged_repository = temporary / "repository"
    staged_catalog = staged_repository / "skills"
    shutil.copytree(catalog, staged_catalog)
    for harness in SUPPORTED_HARNESSES:
        source = repository / "adapters" / harness / "PACKAGING.env"
        destination = staged_repository / "adapters" / harness / "PACKAGING.env"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    manifest_path = staged_catalog / skill_id / "manifest.env"
    values = load_env(manifest_path)
    values["SKILL_VERSION"] = version
    manifest_path.write_text(
        canonical_env(values),
        encoding="utf-8",
        newline="\n",
    )
    return staged_repository, staged_catalog


def _validate_remote_name(value: str) -> None:
    if (
        not REMOTE_NAME_PATTERN.fullmatch(value)
        or ".." in value
        or value.startswith((".", "/"))
        or value.endswith(("/", ".lock"))
    ):
        raise ValueError("remote Git inválido")

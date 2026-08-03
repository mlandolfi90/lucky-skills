from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lifecycle_core.envfile import load_env
from lifecycle_core.harness_catalog import packageable_harness_ids
from lifecycle_core.hashing import sha256_bytes, sha256_file
from lifecycle_core.manifest import Manifest, dependency_closure


PORTABLE_FILES = ("SKILL.md", "manifest.env")
OPTIONAL_PORTABLE_FILES = (".gitattributes",)
PORTABLE_DIRECTORIES = ("assets", "references", "scripts")
IGNORED_SOURCE_NAMES = frozenset(
    {"__pycache__", ".DS_Store", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
)
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class HarnessSpec:
    harness_id: str
    output_kind: str
    skill_prefix: Path
    include_openai_metadata: bool
    archive_suffix: str


@dataclass(frozen=True)
class BuiltArtifact:
    skill_id: str
    logical_path: str
    output_path: Path
    content_hash: str


@dataclass(frozen=True)
class PackagingResult:
    harness_id: str
    skills: tuple[str, ...]
    artifacts: tuple[BuiltArtifact, ...]
    content_hash: str


def package_skills(
    *,
    repository_root: Path,
    catalog_root: Path,
    output_root: Path,
    skill_ids: tuple[str, ...],
    harness_id: str,
) -> PackagingResult:
    """Build a harness projection, expanding each requested skill's dependencies."""
    if not skill_ids:
        raise ValueError("se requiere al menos una skill")
    repository = repository_root.resolve(strict=True)
    catalog = catalog_root.resolve(strict=True)
    destination = output_root.resolve()
    spec = _load_harness_spec(repository, harness_id)
    manifests = _resolve_manifests(catalog, skill_ids)
    for manifest in manifests:
        _validate_source_layout(manifest)

    destination.mkdir(parents=True, exist_ok=True)
    artifacts = tuple(
        _build_artifact(spec, manifest, destination) for manifest in manifests
    )
    records = "".join(
        f"{artifact.logical_path}\0{artifact.content_hash}\n" for artifact in artifacts
    ).encode("utf-8")
    return PackagingResult(
        harness_id=spec.harness_id,
        skills=tuple(manifest.skill_id for manifest in manifests),
        artifacts=artifacts,
        content_hash=sha256_bytes(records),
    )


def _load_harness_spec(repository_root: Path, harness_id: str) -> HarnessSpec:
    if harness_id not in packageable_harness_ids(repository_root):
        raise ValueError(f"harness no soportado: {harness_id}")
    values = load_env(repository_root / "adapters" / harness_id / "PACKAGING.env")
    expected = {
        "FORMAT_VERSION",
        "HARNESS_ID",
        "OUTPUT_KIND",
        "SKILL_PREFIX",
        "INCLUDE_OPENAI_METADATA",
        "ARCHIVE_SUFFIX",
    }
    if set(values) != expected:
        raise ValueError(f"{harness_id}: contrato PACKAGING.env inválido")
    if values["FORMAT_VERSION"] != "1" or values["HARNESS_ID"] != harness_id:
        raise ValueError(f"{harness_id}: identidad de adaptador inválida")
    output_kind = values["OUTPUT_KIND"]
    if output_kind not in {"DIRECTORY", "ZIP_PER_SKILL"}:
        raise ValueError(f"{harness_id}: OUTPUT_KIND inválido")
    include_metadata = values["INCLUDE_OPENAI_METADATA"]
    if include_metadata not in {"YES", "NO"}:
        raise ValueError(f"{harness_id}: INCLUDE_OPENAI_METADATA inválido")
    prefix = _safe_relative_prefix(values["SKILL_PREFIX"])
    suffix = values["ARCHIVE_SUFFIX"]
    if output_kind == "DIRECTORY" and (not prefix.parts or suffix):
        raise ValueError(f"{harness_id}: proyección de directorio inválida")
    if output_kind == "ZIP_PER_SKILL" and (prefix.parts or suffix != ".zip"):
        raise ValueError(f"{harness_id}: proyección ZIP inválida")
    return HarnessSpec(
        harness_id=harness_id,
        output_kind=output_kind,
        skill_prefix=prefix,
        include_openai_metadata=include_metadata == "YES",
        archive_suffix=suffix,
    )


def _resolve_manifests(
    catalog_root: Path, skill_ids: tuple[str, ...]
) -> tuple[Manifest, ...]:
    ordered: list[Manifest] = []
    seen: set[str] = set()
    for skill_id in skill_ids:
        for manifest in dependency_closure(catalog_root, skill_id):
            if manifest.skill_id not in seen:
                seen.add(manifest.skill_id)
                ordered.append(manifest)
    return tuple(ordered)


def _validate_source_layout(manifest: Manifest) -> None:
    if len(manifest.skill_id) > 64:
        raise ValueError(f"{manifest.skill_id}: name supera 64 caracteres")
    allowed = {
        *PORTABLE_FILES,
        *OPTIONAL_PORTABLE_FILES,
        *PORTABLE_DIRECTORIES,
        "agents",
        *IGNORED_SOURCE_NAMES,
    }
    unexpected = sorted(
        path.name for path in manifest.root.iterdir() if path.name not in allowed
    )
    if unexpected:
        raise ValueError(
            f"{manifest.skill_id}: contenido superior no portable: {', '.join(unexpected)}"
        )
    for file_name in PORTABLE_FILES:
        if not (manifest.root / file_name).is_file():
            raise ValueError(f"{manifest.skill_id}: falta {file_name}")
    for directory_name in PORTABLE_DIRECTORIES:
        candidate = manifest.root / directory_name
        if candidate.exists() and not candidate.is_dir():
            raise ValueError(
                f"{manifest.skill_id}: {directory_name} debe ser directorio"
            )
    agents = manifest.root / "agents"
    if agents.exists():
        if not agents.is_dir():
            raise ValueError(f"{manifest.skill_id}: agents debe ser directorio")
        unexpected_agent_files = sorted(
            path.relative_to(agents).as_posix()
            for path in agents.rglob("*")
            if path.is_file() and path.relative_to(agents).as_posix() != "openai.yaml"
        )
        if unexpected_agent_files:
            raise ValueError(
                f"{manifest.skill_id}: metadata de agents no soportada: "
                + ", ".join(unexpected_agent_files)
            )


def _build_artifact(
    spec: HarnessSpec, manifest: Manifest, output_root: Path
) -> BuiltArtifact:
    if spec.output_kind == "ZIP_PER_SKILL":
        return _build_zip(spec, manifest, output_root)
    return _build_directory(spec, manifest, output_root)


def _build_directory(
    spec: HarnessSpec, manifest: Manifest, output_root: Path
) -> BuiltArtifact:
    parent = output_root.joinpath(*spec.skill_prefix.parts)
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / manifest.skill_id
    with tempfile.TemporaryDirectory(
        prefix=f".{manifest.skill_id}.packaging-", dir=parent
    ) as temporary:
        staged = Path(temporary) / manifest.skill_id
        staged.mkdir()
        _copy_skill_files(
            source=manifest.root,
            destination=staged,
            include_openai_metadata=spec.include_openai_metadata,
        )
        staged_hash = _directory_content_hash(staged)
        _replace_directory(staged, target)
    logical = (spec.skill_prefix / manifest.skill_id).as_posix()
    return BuiltArtifact(
        skill_id=manifest.skill_id,
        logical_path=logical,
        output_path=target,
        content_hash=staged_hash,
    )


def _build_zip(
    spec: HarnessSpec, manifest: Manifest, output_root: Path
) -> BuiltArtifact:
    target = output_root / f"{manifest.skill_id}{spec.archive_suffix}"
    file_records = _skill_file_records(
        manifest.root, include_openai_metadata=spec.include_openai_metadata
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{manifest.skill_id}.packaging-",
        suffix=".zip",
        dir=output_root,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
            for relative, source in file_records:
                info = zipfile.ZipInfo(
                    filename=f"{manifest.skill_id}/{relative.as_posix()}",
                    date_time=ZIP_TIMESTAMP,
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source.read_bytes())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return BuiltArtifact(
        skill_id=manifest.skill_id,
        logical_path=target.name,
        output_path=target,
        content_hash=sha256_file(target),
    )


def _copy_skill_files(
    *, source: Path, destination: Path, include_openai_metadata: bool
) -> None:
    for relative, file_path in _skill_file_records(
        source, include_openai_metadata=include_openai_metadata
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file_path, target)


def _skill_file_records(
    source: Path, *, include_openai_metadata: bool
) -> tuple[tuple[Path, Path], ...]:
    records: list[tuple[Path, Path]] = []
    for file_name in PORTABLE_FILES:
        records.append((Path(file_name), source / file_name))
    for file_name in OPTIONAL_PORTABLE_FILES:
        optional = source / file_name
        if optional.is_file():
            records.append((Path(file_name), optional))
    for directory_name in PORTABLE_DIRECTORIES:
        directory = source / directory_name
        if directory.is_dir():
            for file_path in sorted(
                (
                    path
                    for path in directory.rglob("*")
                    if path.is_file() and _is_portable_resource(path, source)
                ),
                key=lambda path: path.relative_to(source).as_posix(),
            ):
                records.append((file_path.relative_to(source), file_path))
    metadata = source / "agents" / "openai.yaml"
    if include_openai_metadata and metadata.is_file():
        records.append((Path("agents/openai.yaml"), metadata))
    return tuple(sorted(records, key=lambda item: item[0].as_posix()))


def _replace_directory(staged: Path, target: Path) -> None:
    backup = target.with_name(f".{target.name}.packaging-backup")
    if backup.exists() or backup.is_symlink():
        raise ValueError(f"backup de empaquetado previo sin resolver: {backup}")
    had_target = target.exists() or target.is_symlink()
    if had_target:
        os.replace(target, backup)
    try:
        os.replace(staged, target)
    except BaseException:
        if (
            had_target
            and (backup.exists() or backup.is_symlink())
            and not (target.exists() or target.is_symlink())
        ):
            os.replace(backup, target)
        raise
    if backup.exists() or backup.is_symlink():
        _remove_path(backup)


def _directory_content_hash(root: Path) -> str:
    records = "".join(
        f"{path.relative_to(root).as_posix()}\0{sha256_file(path)}\n"
        for path in sorted(
            (candidate for candidate in root.rglob("*") if candidate.is_file()),
            key=lambda candidate: candidate.relative_to(root).as_posix(),
        )
    ).encode("utf-8")
    return sha256_bytes(records)


def _is_portable_resource(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return not any(
        part in IGNORED_SOURCE_NAMES for part in relative.parts
    ) and not path.name.endswith((".pyc", ".pyo"))


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _safe_relative_prefix(raw: str) -> Path:
    if not raw:
        return Path()
    normalized = raw.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"prefijo inseguro: {raw!r}")
    return path

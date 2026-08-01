from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from .manifest import Manifest, validate_skill


TODO_PATTERN = re.compile(rb"(?<![A-Z0-9_])TODO(?![A-Z0-9_])")
MARKDOWN_LINK_PATTERN = re.compile(
    r"!?\[[^\]]*]\(\s*(?P<target><[^>]+>|[^)\s]+)",
)
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "data:")


@dataclass(frozen=True, order=True)
class ValidationIssue:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class SuiteValidationReport:
    manifests: tuple[Manifest, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_suite(skills_root: Path) -> SuiteValidationReport:
    catalog = skills_root.resolve(strict=True)
    if not catalog.is_dir():
        raise ValueError(f"{skills_root}: se esperaba un directorio")

    issues: list[ValidationIssue] = []
    manifests: dict[str, Manifest] = {}
    skill_roots: list[Path] = []
    for path in sorted(catalog.iterdir(), key=lambda item: item.name):
        if not path.is_dir():
            continue
        if path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)()):
            issues.append(
                ValidationIssue(
                    "INVALID_SKILL",
                    path.name,
                    "la carpeta de skill no puede ser un enlace",
                )
            )
            continue
        skill_roots.append(path)
    if not skill_roots:
        issues.append(
            ValidationIssue("EMPTY_CATALOG", ".", "no contiene ninguna skill")
        )

    for skill_root in skill_roots:
        try:
            manifest = validate_skill(skill_root)
            if len(manifest.skill_id) > 64:
                issues.append(
                    ValidationIssue(
                        "SKILL_ID_TOO_LONG",
                        skill_root.name,
                        "SKILL_ID excede 64 caracteres",
                    )
                )
            manifests[manifest.skill_id] = manifest
        except (OSError, ValueError) as error:
            issues.append(
                ValidationIssue(
                    "INVALID_SKILL",
                    skill_root.name,
                    str(error),
                )
            )
        issues.extend(_scan_todos(catalog, skill_root))
        issues.extend(_scan_local_references(catalog, skill_root))

    issues.extend(_dependency_issues(catalog, manifests))
    return SuiteValidationReport(
        manifests=tuple(manifests[key] for key in sorted(manifests)),
        issues=tuple(sorted(set(issues))),
    )


def require_valid_suite(skills_root: Path) -> tuple[Manifest, ...]:
    report = validate_suite(skills_root)
    if report.issues:
        summary = "; ".join(
            f"{issue.code}:{issue.path}:{issue.detail}" for issue in report.issues
        )
        raise ValueError(f"suite inválida: {summary}")
    return report.manifests


def _scan_todos(catalog: Path, skill_root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path in _regular_files(skill_root):
        try:
            content = path.read_bytes()
        except OSError as error:
            issues.append(
                ValidationIssue(
                    "UNREADABLE_FILE",
                    _display_path(catalog, path),
                    str(error),
                )
            )
            continue
        if TODO_PATTERN.search(content):
            issues.append(
                ValidationIssue(
                    "TODO_FOUND",
                    _display_path(catalog, path),
                    "contiene un marcador TODO",
                )
            )
    return issues


def _scan_local_references(
    catalog: Path,
    skill_root: Path,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root_resolved = skill_root.resolve(strict=True)
    for markdown in (
        path for path in _regular_files(skill_root) if path.suffix.lower() == ".md"
    ):
        try:
            content = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            issues.append(
                ValidationIssue(
                    "UNREADABLE_MARKDOWN",
                    _display_path(catalog, markdown),
                    str(error),
                )
            )
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(content):
            raw_target = match.group("target").strip("<>")
            if not raw_target or raw_target.startswith("#"):
                continue
            if raw_target.lower().startswith(EXTERNAL_SCHEMES):
                continue
            target_without_fragment = raw_target.split("#", 1)[0].split("?", 1)[0]
            decoded_target = unquote(target_without_fragment)
            portable_target = PurePosixPath(decoded_target.replace("\\", "/"))
            if portable_target.is_absolute() or ".." in portable_target.parts:
                issues.append(
                    ValidationIssue(
                        "REFERENCE_OUTSIDE_SKILL",
                        _display_path(catalog, markdown),
                        raw_target,
                    )
                )
                continue
            candidate = markdown.parent.joinpath(*portable_target.parts)
            resolved = candidate.resolve(strict=False)
            try:
                resolved.relative_to(root_resolved)
            except ValueError:
                issues.append(
                    ValidationIssue(
                        "REFERENCE_OUTSIDE_SKILL",
                        _display_path(catalog, markdown),
                        raw_target,
                    )
                )
                continue
            if not candidate.exists():
                issues.append(
                    ValidationIssue(
                        "MISSING_REFERENCE",
                        _display_path(catalog, markdown),
                        raw_target,
                    )
                )
    return issues


def _dependency_issues(
    catalog: Path,
    manifests: dict[str, Manifest],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    graph: dict[str, tuple[str, ...]] = {}
    for skill_id, manifest in manifests.items():
        valid_dependencies: list[str] = []
        for dependency in manifest.requires:
            available = manifests.get(dependency.skill_id)
            if available is None:
                issues.append(
                    ValidationIssue(
                        "MISSING_DEPENDENCY",
                        skill_id,
                        f"{dependency.skill_id}@{dependency.version}",
                    )
                )
                continue
            if not available.version.satisfies(dependency.version):
                issues.append(
                    ValidationIssue(
                        "DEPENDENCY_VERSION_MISMATCH",
                        skill_id,
                        (
                            f"{dependency.skill_id}: requiere {dependency.version}, "
                            f"disponible {available.version}"
                        ),
                    )
                )
                continue
            valid_dependencies.append(dependency.skill_id)
        graph[skill_id] = tuple(valid_dependencies)

    states: dict[str, int] = {}
    stack: list[str] = []
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(skill_id: str) -> None:
        states[skill_id] = 1
        stack.append(skill_id)
        for dependency in graph.get(skill_id, ()):
            state = states.get(dependency, 0)
            if state == 0:
                visit(dependency)
            elif state == 1:
                start = stack.index(dependency)
                cycle = tuple(stack[start:] + [dependency])
                canonical = _canonical_cycle(cycle)
                if canonical not in reported_cycles:
                    reported_cycles.add(canonical)
                    issues.append(
                        ValidationIssue(
                            "DEPENDENCY_CYCLE",
                            skill_id,
                            " -> ".join(cycle),
                        )
                    )
        stack.pop()
        states[skill_id] = 2

    for skill_id in sorted(graph):
        if states.get(skill_id, 0) == 0:
            visit(skill_id)
    return issues


def _canonical_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    members = cycle[:-1]
    rotations = tuple(
        members[index:] + members[:index] for index in range(len(members))
    )
    return min(rotations)


def _regular_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            name for name in directories if not (current_path / name).is_symlink()
        )
        for name in sorted(names):
            path = current_path / name
            if path.is_file() and not path.is_symlink():
                files.append(path)
    return tuple(files)


def _display_path(catalog: Path, path: Path) -> str:
    return path.relative_to(catalog).as_posix()

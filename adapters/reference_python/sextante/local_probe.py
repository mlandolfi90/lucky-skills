from __future__ import annotations

import os
from pathlib import Path

from .command import GitClient
from .file_fingerprint import fingerprint_files
from .fingerprint_contract import (
    FINGERPRINT_FORMAT,
    canonical_record,
    fingerprint_records,
    portable_path_text,
)
from .git_snapshot import (
    dirty_paths,
    parse_index,
    parse_tree,
)
from .models import LocalObservation


DEFAULT_EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".lifecycle/local",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
}


def probe_local(
    workspace: Path,
    *,
    timeout_seconds: int,
    max_entries: int,
) -> tuple[LocalObservation, GitClient]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace inexistente o no accesible: {workspace}")

    git = GitClient(workspace, timeout_seconds)
    repository = git.query("rev-parse", "--show-toplevel")
    if repository.returncode == 0:
        return _probe_git(
            workspace,
            git,
            max_entries=max_entries,
            timeout_seconds=timeout_seconds,
        ), git
    if not git.available:
        return _probe_workspace(
            workspace,
            max_entries,
            timeout_seconds=timeout_seconds,
            versioning="UNKNOWN",
            force_partial=True,
        ), git
    if "not a git repository" not in repository.stderr.lower():
        return _probe_workspace(
            workspace,
            max_entries,
            timeout_seconds=timeout_seconds,
            versioning="UNKNOWN",
            force_partial=True,
        ), git
    return _probe_workspace(
        workspace,
        max_entries,
        timeout_seconds=timeout_seconds,
        versioning="UNVERSIONED",
        force_partial=False,
    ), git


def _probe_git(
    workspace: Path,
    git: GitClient,
    *,
    max_entries: int,
    timeout_seconds: int,
) -> LocalObservation:
    head_result = git.query("rev-parse", "--verify", "HEAD")
    head = head_result.stdout.strip() if head_result.returncode == 0 else "NO_COMMIT"

    branch_result = git.query("symbolic-ref", "--quiet", "--short", "HEAD")
    branch = (
        branch_result.stdout.strip()
        if branch_result.returncode == 0
        else "DETACHED_OR_UNBORN"
    )
    if not portable_path_text(branch):
        return _git_probe_failure(
            head,
            "UNDECODABLE_BRANCH",
            git,
            "UNSUPPORTED_PATH_TEXT",
        )

    index_result = git.query("ls-files", "--stage", "-z", "--cached")
    untracked_result = git.query(
        "ls-files",
        "-z",
        "--others",
        "--exclude-standard",
    )
    format_result = git.query("rev-parse", "--show-object-format")
    tree_result = (
        git.query("ls-tree", "-r", "-z", "HEAD") if head != "NO_COMMIT" else None
    )
    command_results = [
        index_result,
        untracked_result,
        format_result,
        *([tree_result] if tree_result else []),
    ]
    failed = next(
        (result for result in command_results if result.returncode != 0),
        None,
    )
    if failed is not None:
        scan_status = "OUTPUT_LIMIT" if failed.output_limited else "GIT_SNAPSHOT_ERROR"
        return _git_probe_failure(head, branch, git, scan_status)

    object_format = format_result.stdout.strip()
    if object_format not in {"sha1", "sha256"}:
        return _git_probe_failure(head, branch, git, "OBJECT_FORMAT_UNKNOWN")
    try:
        index = parse_index(index_result.stdout)
        head_tree = parse_tree(tree_result.stdout) if tree_result else ()
    except ValueError:
        return _git_probe_failure(head, branch, git, "GIT_SNAPSHOT_INVALID")

    untracked = tuple(path for path in untracked_result.stdout.split("\0") if path)
    if any(not portable_path_text(path) for path in untracked):
        return _git_probe_failure(head, branch, git, "UNSUPPORTED_PATH_TEXT")
    tracked_paths = tuple(entry.path for entry in index if entry.mode != "160000")
    file_fingerprint = fingerprint_files(
        workspace,
        (*tracked_paths, *untracked),
        max_entries=max_entries,
        timeout_seconds=timeout_seconds,
    )
    fingerprint_status = file_fingerprint.status
    dirty = dirty_paths(
        index=index,
        head_tree=head_tree,
        untracked=untracked,
        blobs=file_fingerprint.blobs,
        object_format=object_format,
    )

    # La huella identifica contenido: rutas y bytes (D-078). Rama, índice y
    # árbol de HEAD son posición en git y se registran aparte (`BRANCH`,
    # `LOCAL_COMMIT`, dirty); incluirlos hacía que adoptar en una rama y
    # mergear a otra produjera DRIFT permanente sin que cambiara un byte.
    material = [
        canonical_record("FORMAT", FINGERPRINT_FORMAT),
        canonical_record("VERSIONING", "GIT"),
        *file_fingerprint.material,
    ]
    return LocalObservation(
        result="ALIGNED" if fingerprint_status == "COMPLETE" else "PARTIAL",
        versioning="NO_COMMIT" if head == "NO_COMMIT" else "GIT",
        fingerprint=fingerprint_records(material),
        head=head,
        branch=branch,
        dirty=bool(dirty),
        dirty_count=len(dirty),
        entry_count=file_fingerprint.entry_count,
        scan_status=fingerprint_status,
        git_safe_override=git.safe_override,
    )


def _git_probe_failure(
    head: str,
    branch: str,
    git: GitClient,
    scan_status: str,
) -> LocalObservation:
    material = (
        canonical_record("FORMAT", FINGERPRINT_FORMAT),
        canonical_record("VERSIONING", "GIT"),
        canonical_record("SCAN_STATUS", scan_status),
    )
    return LocalObservation(
        result="PARTIAL",
        versioning="NO_COMMIT" if head == "NO_COMMIT" else "GIT",
        fingerprint=fingerprint_records(material),
        head=head,
        branch=branch,
        dirty=False,
        dirty_count=0,
        entry_count=0,
        scan_status=scan_status,
        git_safe_override=git.safe_override,
    )


def _probe_workspace(
    workspace: Path,
    max_entries: int,
    *,
    timeout_seconds: int,
    versioning: str,
    force_partial: bool,
) -> LocalObservation:
    relative_paths: list[str] = []
    truncated = False

    for root, directory_names, file_names in os.walk(
        workspace, topdown=True, followlinks=False
    ):
        relative_root = Path(root).relative_to(workspace)
        traversable_directories: list[str] = []
        for name in sorted(directory_names):
            relative_path = relative_root / name
            if _is_excluded(relative_path):
                continue
            if _is_linklike(workspace / relative_path):
                relative_paths.append(relative_path.as_posix())
                if len(relative_paths) > max_entries:
                    truncated = True
                    break
                continue
            traversable_directories.append(name)
        directory_names[:] = traversable_directories
        if truncated:
            break
        for name in sorted(file_names):
            relative_path = relative_root / name
            if _is_excluded(relative_path):
                continue
            relative_paths.append(relative_path.as_posix())
            if len(relative_paths) > max_entries:
                truncated = True
                break
        if truncated:
            break

    file_fingerprint = fingerprint_files(
        workspace,
        relative_paths,
        max_entries=max_entries,
        timeout_seconds=timeout_seconds,
    )
    scan_status = "ENTRY_LIMIT_REACHED" if truncated else file_fingerprint.status
    material = [
        canonical_record("FORMAT", FINGERPRINT_FORMAT),
        canonical_record("VERSIONING", versioning),
        *file_fingerprint.material,
    ]

    return LocalObservation(
        result=(
            "PARTIAL"
            if truncated or force_partial or not file_fingerprint.complete
            else "ALIGNED"
        ),
        versioning=versioning,
        fingerprint=fingerprint_records(material),
        head="NOT_APPLICABLE",
        branch="NOT_APPLICABLE",
        dirty=bool(relative_paths),
        dirty_count=len(relative_paths),
        entry_count=file_fingerprint.entry_count,
        scan_status=scan_status,
        git_safe_override=False,
    )


def _is_excluded(relative_path: Path) -> bool:
    normalized = relative_path.as_posix().strip("/")
    return any(
        normalized == excluded or normalized.startswith(f"{excluded}/")
        for excluded in DEFAULT_EXCLUDED_DIRECTORIES
    )


def _is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()

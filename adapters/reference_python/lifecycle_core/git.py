from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


def git(
    workspace: Path,
    arguments: Iterable[str],
    *,
    timeout: int = 30,
) -> GitResult:
    command = ["git", "-C", str(workspace), *arguments]
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=environment,
    )
    return GitResult(completed.returncode, completed.stdout, completed.stderr)


def clone_repository(
    remote: str,
    destination: Path,
    *,
    branch: str,
    timeout: int = 120,
) -> GitResult:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    completed = subprocess.run(
        [
            "git",
            "-c",
            "protocol.ext.allow=never",
            "clone",
            "--no-tags",
            "--depth=1",
            "--branch",
            branch,
            "--",
            remote,
            str(destination),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=environment,
    )
    return GitResult(completed.returncode, completed.stdout, completed.stderr)


def is_repository(workspace: Path) -> bool:
    result = git(workspace, ("rev-parse", "--is-inside-work-tree"))
    return result.returncode == 0 and result.stdout.strip() == "true"


def worktree_state(workspace: Path) -> str:
    """Separar "no hay repositorio" de "no se pudo leer el repositorio".

    `is_repository` colapsa ambos casos en `False`, así que quien consulta no
    distingue ausencia de evidencia de evidencia inaccesible y tiende a leer el
    segundo caso como el primero. Git informa `not a git repository` tanto para
    un directorio suelto como para un `.git` corrupto, de modo que el
    discriminante es la presencia del propio `.git` en disco.
    """
    result = git(workspace, ("rev-parse", "--is-inside-work-tree"))
    if result.returncode == 0:
        return "REPOSITORY" if result.stdout.strip() == "true" else "NOT_A_REPOSITORY"
    absent = not (workspace / ".git").exists()
    if absent and "not a git repository" in result.stderr.lower():
        return "NOT_A_REPOSITORY"
    return "UNREACHABLE"


def head(workspace: Path) -> str:
    result = git(workspace, ("rev-parse", "HEAD"))
    return result.stdout.strip() if result.returncode == 0 else "NO_COMMIT"


def dirty_paths(workspace: Path, relative_paths: Iterable[str]) -> tuple[str, ...]:
    arguments = ["status", "--porcelain=v1", "--untracked-files=all", "--"]
    arguments.extend(relative_paths)
    result = git(workspace, arguments)
    if result.returncode != 0:
        raise ValueError("no se pudo consultar git status")
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            paths.append(unquote_git_path(line[3:].split(" -> ")[-1]))
    return tuple(sorted(set(paths)))


def all_dirty_paths(workspace: Path) -> tuple[str, ...]:
    result = git(
        workspace,
        ("status", "--porcelain=v1", "--untracked-files=all"),
    )
    if result.returncode != 0:
        raise ValueError("no se pudo consultar git status")
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            paths.append(unquote_git_path(line[3:].split(" -> ")[-1]))
    return tuple(sorted(set(paths)))


_GIT_QUOTE_ESCAPES = {
    "n": 0x0A,
    "t": 0x09,
    "r": 0x0D,
    "\\": 0x5C,
    '"': 0x22,
    "a": 0x07,
    "b": 0x08,
    "f": 0x0C,
    "v": 0x0B,
}


def unquote_git_path(path: str) -> str:
    """Decodificar el C-quoting de git (`"docs/con espacio \\303\\261.md"`).

    Git envuelve en comillas y escapa (octal para no-ASCII) los paths con
    caracteres especiales. Propagar esa forma cruda rompe cualquier consumidor
    que compare contra el nombre real del archivo. Si la secuencia no es
    decodificable, se devuelve el literal original antes que inventar un path.
    """
    if len(path) < 2 or not (path.startswith('"') and path.endswith('"')):
        return path
    body = path[1:-1]
    decoded = bytearray()
    index = 0
    while index < len(body):
        character = body[index]
        if character != "\\":
            decoded.extend(character.encode("utf-8"))
            index += 1
            continue
        index += 1
        if index >= len(body):
            return path
        escape = body[index]
        if escape in _GIT_QUOTE_ESCAPES:
            decoded.append(_GIT_QUOTE_ESCAPES[escape])
            index += 1
            continue
        octal = body[index : index + 3]
        if len(octal) == 3 and all(digit in "01234567" for digit in octal):
            decoded.append(int(octal, 8))
            index += 3
            continue
        return path
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError:
        return path


def commit_paths(
    workspace: Path,
    relative_paths: Iterable[str],
    *,
    message: str,
) -> str:
    paths = tuple(relative_paths)
    add = git(workspace, ("add", "--", *paths))
    if add.returncode != 0:
        raise ValueError(f"git add falló: {add.stderr.strip()}")
    commit = git(workspace, ("commit", "-m", message, "--", *paths), timeout=60)
    if commit.returncode != 0:
        raise ValueError(f"git commit falló: {commit.stderr.strip()}")
    return head(workspace)

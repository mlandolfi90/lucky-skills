from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Iterable


DEFAULT_IGNORED_NAMES = frozenset(
    {
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".DS_Store",
    }
)
MAX_TREE_ENTRIES = 20_000
MAX_FILE_BYTES = 20 * 1024 * 1024


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path, *, max_bytes: int = MAX_FILE_BYTES) -> str:
    metadata = path.lstat()
    if path.is_symlink() or _is_junction(path):
        raise ValueError(f"{path}: enlaces no permitidos")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"{path}: se esperaba un archivo regular")
    if metadata.st_size > max_bytes:
        raise ValueError(f"{path}: archivo demasiado grande")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hash(
    root: Path,
    *,
    ignored_names: Iterable[str] = DEFAULT_IGNORED_NAMES,
    max_entries: int = MAX_TREE_ENTRIES,
    exclude_top: Iterable[str] = (),
) -> str:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{root}: se esperaba un directorio")
    ignored = frozenset(ignored_names)
    # Exclusión SOLO del nivel superior: la usa la proyección de harness para
    # hashear el árbol tal como se instala (p. ej. sin `agents/` en
    # claude-code). No es un ignore global: un `agents/` anidado sí cuenta.
    excluded_top = frozenset(exclude_top)
    records: list[bytes] = []
    entries = 0
    for current, directories, files in os.walk(resolved, followlinks=False):
        current_path = Path(current)
        if excluded_top and current_path == resolved:
            directories[:] = [name for name in directories if name not in excluded_top]
            files = [name for name in files if name not in excluded_top]
        directories[:] = sorted(name for name in directories if name not in ignored)
        for directory in directories:
            child = current_path / directory
            if child.is_symlink() or _is_junction(child):
                raise ValueError(f"{child}: enlaces no permitidos")
        for name in sorted(files):
            if name in ignored or name.endswith((".pyc", ".pyo")):
                continue
            path = current_path / name
            relative = path.relative_to(resolved).as_posix()
            file_hash = sha256_file(path)
            records.append(f"{relative}\0{file_hash}\n".encode("utf-8"))
            entries += 1
            if entries > max_entries:
                raise ValueError(f"{root}: demasiadas entradas")
    digest = hashlib.sha256()
    for record in records:
        digest.update(record)
    return digest.hexdigest()


def _is_junction(path: Path) -> bool:
    return bool(getattr(path, "is_junction", lambda: False)())

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .project_config import read_version


VERSION_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$")
MAX_ADAPTER_FILES = 500
MAX_ADAPTER_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class SourceIdentity:
    skill_version: str
    source_root: Path | None
    version_source: str


def resolve_source_identity(
    *,
    explicit_version: str,
    explicit_source_root: str,
    adapter_root: Path,
) -> SourceIdentity:
    discovered_root = (
        None if explicit_source_root else discover_source_root(adapter_root)
    )
    source_root = (
        Path(explicit_source_root).resolve()
        if explicit_source_root
        else discovered_root
    )
    rooted_version = read_version(source_root) if source_root else ""
    version = explicit_version or rooted_version
    if explicit_version and rooted_version and explicit_version != rooted_version:
        raise ValueError("--skill-version no coincide con VERSION de --source-root")
    if not version:
        raise ValueError("versión no resoluble; use --skill-version o --source-root")
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"versión de skill inválida: {version!r}")
    if explicit_source_root:
        version_source = "SOURCE_ROOT_EXPLICIT"
    elif discovered_root:
        version_source = "SOURCE_ROOT_DISCOVERED"
    else:
        version_source = "EXPLICIT"
    if explicit_version and source_root:
        version_source = f"{version_source}+VERSION_ARGUMENT"
    return SourceIdentity(
        skill_version=version,
        source_root=source_root,
        version_source=version_source,
    )


def discover_source_root(adapter_root: Path) -> Path | None:
    resolved_adapter = adapter_root.resolve()
    for candidate in (resolved_adapter, *resolved_adapter.parents):
        version_path = candidate / "VERSION"
        expected_adapter = candidate / "adapters" / "reference_python"
        if version_path.is_file() and expected_adapter.resolve() == resolved_adapter:
            return candidate
    return None


def adapter_fingerprint(adapter_root: Path) -> str:
    root = adapter_root.resolve()
    if not root.is_dir():
        raise ValueError(f"raíz del adaptador inexistente: {root}")
    entries = tuple(root.rglob("*"))
    linked = tuple(path for path in entries if path.is_symlink())
    if linked:
        raise ValueError(f"enlace no permitido en adaptador: {linked[0]}")
    files = sorted(
        path
        for path in entries
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )
    if not files or len(files) > MAX_ADAPTER_FILES:
        raise ValueError("inventario del adaptador vacío o fuera de límite")

    total_bytes = 0
    digest = hashlib.sha256()
    for path in files:
        try:
            relative = path.relative_to(root).as_posix()
            before = path.stat()
        except OSError as error:
            raise ValueError(f"adaptador no legible: {path}") from error
        if total_bytes + before.st_size > MAX_ADAPTER_BYTES:
            raise ValueError("contenido del adaptador fuera de límite")
        content = _read_stable_file(path, before)
        after = path.stat()
        if (
            before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ino != after.st_ino
        ):
            raise ValueError(f"adaptador cambió durante la lectura: {path}")
        total_bytes += len(content)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _read_stable_file(path: Path, expected) -> bytes:
    chunks: list[bytes] = []
    bytes_read = 0
    with path.open("rb") as stream:
        opened = Path(path).stat()
        if not _same_stat(expected, opened):
            raise ValueError(f"adaptador cambió antes de leer: {path}")
        while chunk := stream.read(1024 * 1024):
            bytes_read += len(chunk)
            if bytes_read > expected.st_size:
                raise ValueError(f"adaptador creció durante la lectura: {path}")
            chunks.append(chunk)
    finished = path.stat()
    if bytes_read != expected.st_size or not _same_stat(expected, finished):
        raise ValueError(f"adaptador cambió durante la lectura: {path}")
    return b"".join(chunks)


def _same_stat(left, right) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )

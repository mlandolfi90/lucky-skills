from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Mapping


KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
MAX_ENV_BYTES = 1_000_000


def load_env(path: Path) -> dict[str, str]:
    """Load a strict, interpolation-free CLAVE=VALOR file."""
    _, values = load_env_document(path)
    return values


def load_env_document(path: Path) -> tuple[str, dict[str, str]]:
    if not path.exists():
        return "", {}
    raw = read_stable_utf8(path, max_bytes=MAX_ENV_BYTES)
    return raw, parse_env(raw, source=str(path))


def parse_env(raw: str, *, source: str = "<memory>") -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if not separator or not KEY_PATTERN.fullmatch(key):
            raise ValueError(f"{source}:{line_number}: asignación inválida")
        if key in values:
            raise ValueError(f"{source}:{line_number}: clave duplicada: {key}")
        value = raw_value.strip()
        if value.startswith('"'):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{source}:{line_number}: valor entre comillas inválido"
                ) from error
            if not isinstance(decoded, str):
                raise ValueError(f"{source}:{line_number}: el valor debe ser texto")
            value = decoded
        values[key] = value
    return values


def canonical_env(values: Mapping[str, object]) -> str:
    lines: list[str] = []
    for key, value in values.items():
        if not KEY_PATTERN.fullmatch(key):
            raise ValueError(f"clave inválida: {key}")
        encoded = json.dumps(str(value), ensure_ascii=False)
        lines.append(f"{key}={encoded}")
    return "\n".join(lines) + ("\n" if lines else "")


def write_immutable_atomic(path: Path, content: str) -> None:
    """Create a file atomically and fail if that name already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as error:
            raise ValueError(f"colisión de archivo inmutable: {path.name}") from error
        except OSError as error:
            raise OSError(
                f"no se pudo crear el archivo inmutable sin sobrescritura: {path}"
            ) from error
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def read_stable_utf8(path: Path, *, max_bytes: int) -> str:
    """Read one regular UTF-8 file without following links or accepting races."""
    if max_bytes <= 0:
        raise ValueError("max_bytes debe ser positivo")
    if _is_linklike(path):
        raise ValueError(f"{path}: enlaces no permitidos")
    try:
        before = path.lstat()
    except OSError as error:
        raise ValueError(f"{path}: archivo no accesible") from error
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"{path}: se esperaba un archivo regular")
    if before.st_size > max_bytes:
        raise ValueError(f"{path}: archivo UTF-8 demasiado grande")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not _same_stat(before, opened):
            raise ValueError(f"{path}: cambió antes de la lectura")
        chunks: list[bytes] = []
        bytes_read = 0
        while bytes_read <= max_bytes:
            chunk = os.read(
                descriptor,
                min(64 * 1024, max_bytes + 1 - bytes_read),
            )
            if not chunk:
                break
            chunks.append(chunk)
            bytes_read += len(chunk)
        content = b"".join(chunks)
        if len(content) > max_bytes:
            raise ValueError(f"{path}: archivo UTF-8 demasiado grande")
        finished = os.fstat(descriptor)
        if not _same_stat(opened, finished) or len(content) != finished.st_size:
            raise ValueError(f"{path}: cambió durante la lectura")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path}: UTF-8 inválido") from error


def _same_stat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_mode == right.st_mode
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )


def _is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()

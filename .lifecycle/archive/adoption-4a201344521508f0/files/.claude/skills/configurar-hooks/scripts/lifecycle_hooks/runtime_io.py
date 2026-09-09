from __future__ import annotations

import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_immutable_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
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
            raise ValueError(f"colisión de comprobante: {path.name}") from error
        except OSError as error:
            raise OSError(
                f"no se pudo crear el comprobante sin sobrescritura: {path}"
            ) from error
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def read_stable_utf8(path: Path, *, max_bytes: int) -> str:
    if max_bytes <= 0:
        raise ValueError("max_bytes debe ser positivo")
    if _is_linklike(path):
        raise ValueError(f"{path}: enlaces no permitidos")
    try:
        before = path.lstat()
    except OSError as error:
        raise ValueError(f"{path}: comprobante no accesible") from error
    if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
        raise ValueError(f"{path}: comprobante inválido o demasiado grande")

    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not _same_stat(before, opened):
            raise ValueError(f"{path}: cambió antes de la lectura")
        content = os.read(descriptor, max_bytes + 1)
        finished = os.fstat(descriptor)
        if (
            len(content) > max_bytes
            or not _same_stat(opened, finished)
            or len(content) != finished.st_size
        ):
            raise ValueError(f"{path}: cambió o excede el límite")
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

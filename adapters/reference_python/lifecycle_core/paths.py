from __future__ import annotations

import os
from pathlib import Path, PurePosixPath


WINDOWS_FORBIDDEN = frozenset('<>:"|?*')
WINDOWS_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)


def normalize_relative(value: str) -> Path:
    normalized = value.replace("\\", "/").strip("/")
    candidate = PurePosixPath(normalized)
    if (
        not normalized
        or candidate.is_absolute()
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or any(not _portable_segment(part) for part in candidate.parts)
    ):
        raise ValueError(f"ruta relativa inválida: {value!r}")
    return Path(*candidate.parts)


def _portable_segment(value: str) -> bool:
    stem = value.partition(".")[0].upper()
    return (
        bool(value)
        and not value.endswith((" ", "."))
        and stem not in WINDOWS_RESERVED
        and not any(character in WINDOWS_FORBIDDEN for character in value)
        and not any(ord(character) < 32 for character in value)
    )


def resolve_within(root: Path, relative: str | Path) -> Path:
    root_resolved = root.resolve(strict=True)
    relative_path = (
        normalize_relative(relative)
        if isinstance(relative, str)
        else normalize_relative(relative.as_posix())
    )
    candidate = root_resolved / relative_path
    _reject_existing_links(root_resolved, candidate)
    resolved = candidate.resolve(strict=False)
    if not _is_relative_to(resolved, root_resolved):
        raise ValueError(f"ruta fuera del TARGET: {relative_path}")
    return candidate


def relative_to_root(root: Path, path: Path) -> str:
    root_resolved = root.resolve(strict=True)
    resolved = path.resolve(strict=False)
    if not _is_relative_to(resolved, root_resolved):
        raise ValueError(f"{path}: ruta fuera del TARGET")
    return resolved.relative_to(root_resolved).as_posix()


def ensure_regular_tree(root: Path) -> None:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{root}: se esperaba un directorio")
    for current, directories, files in os.walk(resolved, followlinks=False):
        current_path = Path(current)
        for name in (*directories, *files):
            path = current_path / name
            if path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)()):
                raise ValueError(f"{path}: enlaces no permitidos")


def _reject_existing_links(root: Path, candidate: Path) -> None:
    current = root
    for part in candidate.relative_to(root).parts:
        current /= part
        if current.exists() and (
            current.is_symlink()
            or bool(getattr(current, "is_junction", lambda: False)())
        ):
            raise ValueError(f"{current}: enlace no permitido")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False

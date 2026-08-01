from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .envfile import canonical_env


@contextmanager
def directory_lock(path: Path, owner: dict[str, object]) -> Iterator[Path]:
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise ValueError(f"lock activo: {path}") from error
    (path / "owner.env").write_text(
        canonical_env(owner),
        encoding="utf-8",
        newline="\n",
    )
    try:
        yield path
    finally:
        if path.exists():
            shutil.rmtree(path)

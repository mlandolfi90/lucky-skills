from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .authority import is_human_actor
from .component_contracts import valid_policy, valid_sources, valid_state_map
from .envfile import canonical_env, load_env_document


@dataclass(frozen=True)
class ProjectConfig:
    lifecycle_status: str
    policy: dict[str, str]
    policy_status: str
    sources: dict[str, str]
    sources_status: str
    state_map: dict[str, str]
    state_map_status: str

    @property
    def status(self) -> str:
        statuses = (
            self.policy_status,
            self.sources_status,
            self.state_map_status,
        )
        return "INVALID" if "INVALID" in statuses else "VALID"

    @property
    def baseline_ready(self) -> bool:
        if self.lifecycle_status == "NOT_ADOPTED":
            return True
        return self.lifecycle_status == "ADOPTED" and self.state_map_status == "LOADED"

    @property
    def adopted(self) -> bool:
        return self.lifecycle_status == "ADOPTED"


def load_project_config(workspace: Path) -> ProjectConfig:
    lifecycle = workspace / ".lifecycle"
    if not os.path.lexists(lifecycle):
        return ProjectConfig("NOT_ADOPTED", {}, "ABSENT", {}, "ABSENT", {}, "ABSENT")
    if not lifecycle.is_dir() or _contains_symlink(lifecycle, workspace):
        return ProjectConfig("INVALID", {}, "INVALID", {}, "INVALID", {}, "INVALID")

    policy, policy_status = _load_component(
        lifecycle / "config" / "SEXTANTE.env", workspace, valid_policy
    )
    sources, sources_status = _load_component(
        lifecycle / "config" / "SOURCES.env", workspace, valid_sources
    )
    state_map, state_map_status = _load_component(
        lifecycle / "state" / "STATE-MAP.env", workspace, valid_state_map
    )
    if (policy_status, sources_status, state_map_status) == (
        "ABSENT",
        "ABSENT",
        "ABSENT",
    ):
        # Un `.lifecycle/` sin ninguno de sus tres componentes es un directorio
        # vacío, no una adopción. Clasificarlo como `ADOPTED` lo deja en un
        # estado sin salida: `baseline_ready` es falso mientras el STATE-MAP no
        # esté cargado, y escribirlo a mano mueve la huella local a `DRIFT`, que
        # también bloquea. `NOT_ADOPTED` con los tres `ABSENT` es además lo que
        # exige el contrato del comprobante.
        return ProjectConfig("NOT_ADOPTED", {}, "ABSENT", {}, "ABSENT", {}, "ABSENT")
    return ProjectConfig(
        lifecycle_status="ADOPTED",
        policy=policy,
        policy_status=policy_status,
        sources=sources,
        sources_status=sources_status,
        state_map=state_map,
        state_map_status=state_map_status,
    )


def resolve_readme_policy(
    explicit_policy: str | None,
    confirmed_by: str,
) -> tuple[str, str, str]:
    if explicit_policy:
        if confirmed_by and not is_human_actor(confirmed_by):
            raise ValueError("autoridad de README debe identificar un actor human:")
        if explicit_policy != "IGNORE" and not confirmed_by:
            raise ValueError("elevar confianza del README requiere confirmación human:")
        return (
            explicit_policy,
            "SESSION_HUMAN" if explicit_policy != "IGNORE" else "SESSION_OVERRIDE",
            confirmed_by or "UNCONFIRMED",
        )
    return "IGNORE", "DEFAULT", "UNCONFIRMED"


def positive_int(value: str | None, *, default: int, maximum: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    if parsed <= 0:
        return default
    return min(parsed, maximum)


def csv_values(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def read_version(source_root: Path) -> str:
    path = source_root / "VERSION"
    if path.stat().st_size > 128:
        raise ValueError("VERSION fuera de límite")
    value = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,63}", value):
        raise ValueError(f"VERSION inválida: {value!r}")
    return value


def _contains_symlink(path: Path, workspace: Path) -> bool:
    workspace = workspace.resolve()
    candidate = path
    while candidate != workspace:
        if _is_linklike(candidate):
            return True
        if candidate.parent == candidate:
            return True
        candidate = candidate.parent
    return False


def _load_component(
    path: Path,
    workspace: Path,
    validator,
) -> tuple[dict[str, str], str]:
    if not os.path.lexists(path):
        return {}, "ABSENT"
    if _contains_symlink(path, workspace):
        return {}, "INVALID"
    try:
        raw, values = load_env_document(path)
        if canonical_env(values) != raw:
            return {}, "INVALID"
        return (values, "LOADED") if validator(values) else ({}, "INVALID")
    except (OSError, ValueError):
        return {}, "INVALID"


def _is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or is_junction()

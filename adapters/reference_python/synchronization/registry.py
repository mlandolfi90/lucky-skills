from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from lifecycle_core.envfile import load_env
from lifecycle_core.manifest import SKILL_ID_PATTERN


BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
SCP_REMOTE_PATTERN = re.compile(r"^(?:[A-Za-z0-9._-]+@)?[A-Za-z0-9.-]+:[^\s]+$")
HARNESSES = {"generic", "claude-code", "claude-ai", "codex"}
ALLOWED_REMOTE_SCHEMES = {"file", "git", "https", "ssh"}


@dataclass(frozen=True)
class RepositoryEntry:
    repo_id: str
    remote_url: str
    default_branch: str
    harness: str
    skills: tuple[str, ...]
    status: str

    def includes(self, skill_id: str) -> bool:
        return "*" in self.skills or skill_id in self.skills


def load_registry(registry_root: Path) -> tuple[RepositoryEntry, ...]:
    root = registry_root.resolve(strict=True)
    entries: list[RepositoryEntry] = []
    seen: set[str] = set()
    for path in sorted(root.glob("*.env")):
        values = load_env(path)
        expected = {
            "FORMAT_VERSION",
            "REPO_ID",
            "REMOTE_URL",
            "DEFAULT_BRANCH",
            "HARNESS",
            "SKILLS",
            "STATUS",
        }
        if set(values) != expected or values["FORMAT_VERSION"] != "1":
            raise ValueError(f"{path.name}: contrato de registry inválido")
        repo_id = values["REPO_ID"]
        if (
            not SKILL_ID_PATTERN.fullmatch(repo_id)
            or path.stem != repo_id
            or repo_id in seen
        ):
            raise ValueError(f"{path.name}: REPO_ID inválido o duplicado")
        seen.add(repo_id)
        remote = _remote_without_embedded_credentials(values["REMOTE_URL"])
        branch = _validated_branch(values["DEFAULT_BRANCH"])
        harness = values["HARNESS"]
        if harness not in HARNESSES:
            raise ValueError(f"{path.name}: HARNESS no soportado")
        skills = _skills(values["SKILLS"])
        status = values["STATUS"]
        if status not in {"ACTIVE", "PAUSED"}:
            raise ValueError(f"{path.name}: STATUS inválido")
        entries.append(
            RepositoryEntry(
                repo_id=repo_id,
                remote_url=remote,
                default_branch=branch,
                harness=harness,
                skills=skills,
                status=status,
            )
        )
    return tuple(entries)


def _remote_without_embedded_credentials(value: str) -> str:
    if not value or any(character in value for character in "\r\n\0"):
        raise ValueError("REMOTE_URL inválido")
    if "::" in value:
        raise ValueError("REMOTE_URL usa un helper Git no permitido")
    local_path = Path(value)
    if local_path.is_absolute():
        return value
    parsed = urlsplit(value)
    if not parsed.scheme:
        if SCP_REMOTE_PATTERN.fullmatch(value):
            return value
        raise ValueError("REMOTE_URL debe ser absoluta o usar un transporte permitido")
    if parsed.scheme.lower() not in ALLOWED_REMOTE_SCHEMES:
        raise ValueError("REMOTE_URL usa un transporte no permitido")
    if parsed.password is not None or (
        parsed.username is not None and parsed.scheme.lower() not in {"ssh"}
    ):
        raise ValueError("REMOTE_URL no puede contener credenciales")
    if parsed.query or parsed.fragment:
        raise ValueError("REMOTE_URL no puede contener query ni fragment")
    return value


def _validated_branch(value: str) -> str:
    invalid = (
        not BRANCH_PATTERN.fullmatch(value)
        or ".." in value
        or "//" in value
        or value.endswith(("/", ".", ".lock"))
        or any(character in value for character in "~^:?*[\\")
    )
    if invalid:
        raise ValueError("DEFAULT_BRANCH inválida")
    return value


def _skills(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items or len(set(items)) != len(items):
        raise ValueError("SKILLS vacío o duplicado")
    if "*" in items and len(items) != 1:
        raise ValueError("SKILLS=* no se mezcla con IDs")
    if any(item != "*" and not SKILL_ID_PATTERN.fullmatch(item) for item in items):
        raise ValueError("SKILLS contiene un ID inválido")
    return items

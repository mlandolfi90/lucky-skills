from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .envfile import load_env
from .hashing import tree_hash


SKILL_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)\.(?P<patch>0|[1-9][0-9]*)$"
)
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> Version:
        match = SEMVER_PATTERN.fullmatch(value)
        if not match:
            raise ValueError(f"SemVer inválido: {value!r}")
        return cls(*(int(match.group(name)) for name in ("major", "minor", "patch")))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump(self, impact: str) -> Version:
        normalized = impact.upper()
        if normalized == "PATCH":
            return Version(self.major, self.minor, self.patch + 1)
        if normalized == "MINOR":
            return Version(self.major, self.minor + 1, 0)
        if normalized == "MAJOR":
            return Version(self.major + 1, 0, 0)
        raise ValueError(f"impacto inválido: {impact}")

    def satisfies(self, required: Version) -> bool:
        """Compatibilidad SemVer según D-060: PATCH y MINOR son compatibles.

        `1.0.3` satisface `@1.0.0`; solo un MAJOR distinto — adaptación
        obligatoria — o una versión anterior a la requerida rompen. Con pin
        exacto, cada PATCH de una skill base dejaba el catálogo entero en
        `DEPENDENCY_VERSION_MISMATCH` y obligaba a republicar en cadena.
        """
        return self.major == required.major and self >= required


@dataclass(frozen=True)
class Dependency:
    skill_id: str
    version: Version


@dataclass(frozen=True)
class Manifest:
    skill_id: str
    version: Version
    requires: tuple[Dependency, ...]
    root: Path
    content_hash: str


def load_manifest(skill_root: Path) -> Manifest:
    root = skill_root.resolve(strict=True)
    values = load_env(root / "manifest.env")
    expected_keys = {"FORMAT_VERSION", "SKILL_ID", "SKILL_VERSION", "REQUIRES"}
    if set(values) != expected_keys:
        raise ValueError("manifest.env debe contener solo los cuatro campos canónicos")
    if values["FORMAT_VERSION"] != "1":
        raise ValueError("FORMAT_VERSION no soportado")
    skill_id = values["SKILL_ID"]
    if not SKILL_ID_PATTERN.fullmatch(skill_id) or root.name != skill_id:
        raise ValueError("SKILL_ID inválido o distinto de la carpeta")
    version = Version.parse(values["SKILL_VERSION"])
    requires = _parse_dependencies(values["REQUIRES"])
    return Manifest(
        skill_id=skill_id,
        version=version,
        requires=requires,
        root=root,
        content_hash=tree_hash(root),
    )


def validate_skill(skill_root: Path) -> Manifest:
    manifest = load_manifest(skill_root)
    skill_md = manifest.root / "SKILL.md"
    raw = skill_md.read_text(encoding="utf-8")
    frontmatter = FRONTMATTER_PATTERN.match(raw)
    if not frontmatter:
        raise ValueError("SKILL.md: frontmatter ausente")
    values = _parse_frontmatter(frontmatter.group("body"))
    if set(values) != {"name", "description"}:
        raise ValueError("SKILL.md: usar solo name y description")
    if values["name"] != manifest.skill_id:
        raise ValueError("SKILL.md: name no coincide con manifest.env")
    description = values["description"].strip()
    if not description or len(description) > 200:
        raise ValueError("SKILL.md: description debe tener entre 1 y 200 caracteres")
    return manifest


def dependency_closure(catalog_root: Path, skill_id: str) -> tuple[Manifest, ...]:
    catalog = catalog_root.resolve(strict=True)
    ordered: list[Manifest] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(current_id: str) -> None:
        if current_id in visiting:
            raise ValueError(f"ciclo de dependencias en {current_id}")
        if current_id in visited:
            return
        visiting.add(current_id)
        manifest = validate_skill(catalog / current_id)
        for dependency in manifest.requires:
            dependency_manifest = validate_skill(catalog / dependency.skill_id)
            if not dependency_manifest.version.satisfies(dependency.version):
                raise ValueError(
                    f"{current_id}: versión requerida de {dependency.skill_id} no disponible"
                )
            visit(dependency.skill_id)
        visiting.remove(current_id)
        visited.add(current_id)
        ordered.append(manifest)

    visit(skill_id)
    return tuple(ordered)


def _parse_dependencies(raw: str) -> tuple[Dependency, ...]:
    if not raw:
        return ()
    dependencies: list[Dependency] = []
    seen: set[str] = set()
    for item in raw.split(","):
        skill_id, separator, version = item.strip().partition("@")
        if (
            not separator
            or not SKILL_ID_PATTERN.fullmatch(skill_id)
            or skill_id in seen
        ):
            raise ValueError(f"dependencia inválida: {item!r}")
        seen.add(skill_id)
        dependencies.append(Dependency(skill_id, Version.parse(version)))
    return tuple(dependencies)


def _parse_frontmatter(raw: str) -> dict[str, str]:
    values: dict[str, str] = {}
    current_key = ""
    current_lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith((" ", "\t")) and current_key:
            current_lines.append(line.strip())
            continue
        if current_key:
            values[current_key] = " ".join(current_lines).strip()
        key, separator, value = line.partition(":")
        if not separator or not key.strip():
            raise ValueError("SKILL.md: frontmatter inválido")
        current_key = key.strip()
        current_lines = [value.strip().lstrip(">-").strip()]
    if current_key:
        values[current_key] = " ".join(current_lines).strip()
    return values

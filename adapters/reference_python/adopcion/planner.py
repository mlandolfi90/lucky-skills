from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import replace
from pathlib import Path

from lifecycle_core.git import dirty_paths, is_repository
from lifecycle_core.envfile import canonical_env, load_env
from lifecycle_core.harness_catalog import load_harnesses
from lifecycle_core.hashing import sha256_file, tree_hash
from lifecycle_core.manifest import dependency_closure, validate_skill
from lifecycle_core.paths import normalize_relative, resolve_within

from .landing import validate_landing
from .models import AdoptionPlan, PlanItem


# El eje de harnesses no vive acá: lo declara cada `adapters/<harness>/
# PACKAGING.env` y lo sirve `harness_catalog`. Antes eran dos tablas a mano
# —prefijo y exclusiones— que había que acordarse de tocar en cada harness
# nuevo, con el mismo dato ya escrito en la carpeta del adaptador.
SENSITIVE_PARTS = ("secret", "password", "token", "credential", "private")
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
MAX_ARCHIVE_FILE_BYTES = 5 * 1024 * 1024


def build_plan(
    *,
    source_skill: Path,
    target: Path,
    harness: str,
    landing_receipt: Path,
    legacy_paths: tuple[str, ...] = (),
) -> AdoptionPlan:
    source = source_skill.resolve(strict=True)
    target_resolved = target.resolve(strict=True)
    harnesses = load_harnesses(source.parent.parent)
    if harness not in harnesses:
        raise ValueError(f"harness no soportado: {harness}")
    spec = harnesses[harness]
    landing = validate_landing(landing_receipt, target_resolved)
    root_manifest = validate_skill(source)
    closure = dependency_closure(source.parent, root_manifest.skill_id)
    items: list[PlanItem] = []

    for manifest in closure:
        canonical_item = _directory_item(
            manifest.root,
            target_resolved,
            f"skills/{manifest.skill_id}",
            manifest.skill_id,
            "CANONICAL",
        )
        items.append(canonical_item)
        projection_root = spec.skill_prefix
        if projection_root:
            items.append(
                _directory_item(
                    manifest.root,
                    target_resolved,
                    f"{projection_root}/{manifest.skill_id}",
                    manifest.skill_id,
                    "HARNESS",
                    exclude_top=spec.projection_excludes,
                )
            )
        items.append(
            _state_item(
                target_resolved,
                skill_id=manifest.skill_id,
                version=str(manifest.version),
                # Forma canónica de la plantilla (`skills/<id>`), no la ruta
                # absoluta de esta máquina: el estado adoptado se versiona y se
                # pushea a cada destino, y una ruta absoluta filtra el usuario
                # local y rompe la comparación remota de D-058.
                source=f"skills/{manifest.skill_id}",
                content_hash=canonical_item.source_hash,
                harness=harness,
            )
        )

    lifecycle_ignore = target_resolved / ".lifecycle" / ".gitignore"
    items.append(_gitignore_item(lifecycle_ignore))
    lifecycle_attributes = target_resolved / ".lifecycle" / ".gitattributes"
    items.append(_gitattributes_item(lifecycle_attributes))
    items.append(
        _state_map_item(
            target_resolved,
            landing_fingerprint=landing["LOCAL_FINGERPRINT_FINISHED"],
        )
    )

    seen_legacy: set[str] = set()
    for raw_path in legacy_paths:
        relative = normalize_relative(raw_path).as_posix()
        if relative in seen_legacy:
            raise ValueError(f"legacy path duplicado: {relative}")
        seen_legacy.add(relative)
        destination = resolve_within(target_resolved, relative)
        if destination.exists():
            items.append(
                PlanItem(
                    skill_id=root_manifest.skill_id,
                    role="LEGACY",
                    source="",
                    destination=relative,
                    action="ARCHIVE_REMOVE",
                    source_hash="REMOVED",
                    current_hash=_path_hash(destination),
                )
            )

    # Si cualquier otro ítem cambia el árbol, el STATE-MAP no puede quedar
    # `UNCHANGED` aunque su huella coincida con el aterrizaje: esa huella es la
    # de ANTES de instalar, y tras la instalación quedaría desactualizada — la
    # validación final la rechaza. Con la huella V3 este camino era
    # inalcanzable (nunca coincidía); con V4 es el caso normal de una
    # actualización sobre un repo ya adoptado.
    state_map_index = next(
        index for index, item in enumerate(items) if item.role == "STATE_MAP"
    )
    others_change = any(
        item.action != "UNCHANGED"
        for index, item in enumerate(items)
        if index != state_map_index
    )
    if others_change and items[state_map_index].action == "UNCHANGED":
        items[state_map_index] = replace(
            items[state_map_index], action="ARCHIVE_REPLACE"
        )

    # El STATE-MAP queda fuera del escaneo de colisiones: es estado que la
    # propia transacción gestiona y reescribe, y su legitimidad la corrobora
    # el aterrizaje (una edición ajena muere ahí, antes de llegar acá). Tras
    # `revalidar`, el STATE-MAP modificado sin commitear es acto de gobernanza
    # con recibo, no trabajo ajeno — contarlo era un falso positivo.
    affected = tuple(
        item.destination
        for item in items
        if item.action != "UNCHANGED" and item.role != "STATE_MAP"
    )
    collisions: tuple[str, ...] = ()
    if affected and is_repository(target_resolved):
        collisions = dirty_paths(target_resolved, affected)

    risks = tuple(
        sorted(
            {
                risk
                for item in items
                if item.action in {"ARCHIVE_REPLACE", "ARCHIVE_REMOVE"}
                for risk in _scan_risks(
                    resolve_within(target_resolved, item.destination)
                )
            }
        )
    )
    plan = AdoptionPlan(
        source_skill=str(source),
        target=str(target_resolved),
        skill_id=root_manifest.skill_id,
        skill_version=str(root_manifest.version),
        harness=harness,
        landing_receipt=str(landing_receipt.resolve(strict=True)),
        target_fingerprint=landing["LOCAL_FINGERPRINT_FINISHED"],
        dependencies=tuple(
            f"{manifest.skill_id}@{manifest.version}" for manifest in closure
        ),
        items=tuple(items),
        collisions=collisions,
        risks=risks,
    )
    return plan.with_hash()


def _directory_item(
    source: Path,
    target: Path,
    destination: str,
    skill_id: str,
    role: str,
    exclude_top: tuple[str, ...] = (),
) -> PlanItem:
    # El hash de la fuente describe lo que se va a INSTALAR: para una
    # proyección filtrada, el árbol fuente sin sus exclusiones de tope.
    # El hash del destino existente se toma completo a propósito: una
    # proyección vieja que aún carga `agents/` debe salir ARCHIVE_REPLACE,
    # nunca UNCHANGED.
    source_hash = tree_hash(source, exclude_top=exclude_top)
    target_path = resolve_within(target, destination)
    if not target_path.exists():
        action = "CREATE"
        current_hash = "MISSING"
    elif not target_path.is_dir():
        action = "BLOCK"
        current_hash = _path_hash(target_path)
    else:
        current_hash = tree_hash(target_path)
        action = "UNCHANGED" if current_hash == source_hash else "ARCHIVE_REPLACE"
    removes: tuple[str, ...] = ()
    if action == "ARCHIVE_REPLACE":
        removes = _files_absent_in_source(source, target_path)
    return PlanItem(
        skill_id=skill_id,
        role=role,
        source=str(source),
        destination=destination,
        action=action,
        source_hash=source_hash,
        current_hash=current_hash,
        removes=removes,
    )


def _files_absent_in_source(source: Path, target_path: Path) -> tuple[str, ...]:
    absent: list[str] = []
    for current in target_path.rglob("*"):
        if not current.is_file():
            continue
        relative = current.relative_to(target_path)
        if not (source / relative).is_file():
            absent.append(relative.as_posix())
    # Orden por puntos de código de la ruta posix: el orden de Path es
    # case-insensitive en Windows y el plan debe ser idéntico entre plataformas.
    return tuple(sorted(absent))


def _gitignore_item(destination: Path) -> PlanItem:
    return _static_file_item(
        destination,
        destination_text=".lifecycle/.gitignore",
        role="LIFECYCLE_IGNORE",
        expected=b"local/\n",
    )


def _gitattributes_item(destination: Path) -> PlanItem:
    return _static_file_item(
        destination,
        destination_text=".lifecycle/.gitattributes",
        role="LIFECYCLE_ATTRIBUTES",
        expected=b"* text=auto eol=lf\n",
    )


def _static_file_item(
    destination: Path,
    *,
    destination_text: str,
    role: str,
    expected: bytes,
) -> PlanItem:
    expected_hash = hashlib.sha256(expected).hexdigest()
    if not destination.exists():
        action = "CREATE"
        current_hash = "MISSING"
    elif not destination.is_file():
        action = "BLOCK"
        current_hash = _path_hash(destination)
    else:
        current_hash = sha256_file(destination)
        action = "UNCHANGED" if current_hash == expected_hash else "ARCHIVE_REPLACE"
    return PlanItem(
        skill_id="lifecycle",
        role=role,
        source="",
        destination=destination_text,
        action=action,
        source_hash=expected_hash,
        current_hash=current_hash,
    )


def _state_item(
    target: Path,
    *,
    skill_id: str,
    version: str,
    source: str,
    content_hash: str,
    harness: str,
) -> PlanItem:
    destination_text = f".lifecycle/state/skills/{skill_id}.env"
    destination = resolve_within(target, destination_text)
    expected = {
        "SKILL_ID": skill_id,
        "SKILL_VERSION": version,
        "SOURCE": source,
        "HARNESSES": harness,
        "STATUS": "ACTIVE",
        "CONTENT_HASH": content_hash,
    }
    expected_hash = hashlib.sha256(canonical_env(expected).encode("utf-8")).hexdigest()
    if not destination.exists():
        action = "CREATE"
        current_hash = "MISSING"
    elif not destination.is_file():
        action = "BLOCK"
        current_hash = _path_hash(destination)
    else:
        try:
            values = load_env(destination)
            observed = {key: values.get(key, "") for key in expected}
            current_hash = hashlib.sha256(
                canonical_env(observed).encode("utf-8")
            ).hexdigest()
            action = "UNCHANGED" if observed == expected else "ARCHIVE_REPLACE"
        except ValueError:
            current_hash = sha256_file(destination)
            action = "ARCHIVE_REPLACE"
    return PlanItem(
        skill_id=skill_id,
        role="STATE",
        source=source,
        destination=destination_text,
        action=action,
        source_hash=expected_hash,
        current_hash=current_hash,
    )


def _state_map_item(target: Path, *, landing_fingerprint: str) -> PlanItem:
    destination_text = ".lifecycle/state/STATE-MAP.env"
    destination = resolve_within(target, destination_text)
    expected_hash = f"GENERATED:{landing_fingerprint}"
    if not destination.exists():
        action = "CREATE"
        current_hash = "MISSING"
    elif not destination.is_file():
        action = "BLOCK"
        current_hash = _path_hash(destination)
    else:
        try:
            values = load_env(destination)
            current_hash = sha256_file(destination)
            action = (
                "UNCHANGED"
                if values.get("STATE_SCHEMA") == "1"
                and values.get("GIT_LOCAL_FINGERPRINT") == landing_fingerprint
                else "ARCHIVE_REPLACE"
            )
        except ValueError:
            current_hash = sha256_file(destination)
            action = "ARCHIVE_REPLACE"
    return PlanItem(
        skill_id="lifecycle",
        role="STATE_MAP",
        source="",
        destination=destination_text,
        action=action,
        source_hash=expected_hash,
        current_hash=current_hash,
    )


def _path_hash(path: Path) -> str:
    if path.is_dir():
        return tree_hash(path)
    if path.is_file():
        return sha256_file(path)
    raise ValueError(f"{path}: tipo de ruta no soportado")


def _scan_risks(root: Path) -> tuple[str, ...]:
    paths = [root]
    if root.is_dir():
        paths = []
        for current, directories, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            for name in directories:
                child = current_path / name
                if child.is_symlink():
                    paths.append(child)
            paths.extend(current_path / name for name in files)
    risks: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        metadata = path.lstat()
        if path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)()):
            risks.append(f"LINK:{path.name}")
            continue
        if not stat.S_ISREG(metadata.st_mode):
            continue
        name = path.name.lower()
        if name != "manifest.env" and (
            any(part in name for part in SENSITIVE_PARTS)
            or name.endswith(SENSITIVE_SUFFIXES)
            or name == ".env"
        ):
            risks.append(f"SENSITIVE:{path.name}")
        if metadata.st_size > MAX_ARCHIVE_FILE_BYTES:
            risks.append(f"LARGE:{path.name}:{metadata.st_size}")
    return tuple(risks)

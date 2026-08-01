from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from lifecycle_core.envfile import load_env
from lifecycle_core.git import dirty_paths, worktree_state
from lifecycle_core.paths import normalize_relative


@dataclass(frozen=True)
class Collision:
    kind: str
    subject: str
    actor: str
    source: str


@dataclass(frozen=True)
class CollisionReport:
    state: str
    paths: tuple[str, ...]
    symbols: tuple[str, ...]
    contracts: tuple[str, ...]
    criteria: tuple[str, ...]
    actors: tuple[str, ...]
    base_mismatch: str
    recommendation: str
    collisions: tuple[Collision, ...]


def scan_collisions(
    *,
    workspace: Path,
    paths: tuple[str, ...],
    symbols: tuple[str, ...] = (),
    contracts: tuple[str, ...] = (),
    criteria: tuple[str, ...] = (),
    base_fingerprint: str = "",
) -> CollisionReport:
    root = workspace.resolve(strict=True)
    normalized_paths = tuple(
        sorted({normalize_relative(path).as_posix() for path in paths})
    )
    normalized_symbols = tuple(
        sorted({value.strip() for value in symbols if value.strip()})
    )
    normalized_contracts = tuple(
        sorted({value.strip() for value in contracts if value.strip()})
    )
    normalized_criteria = _criteria(criteria)
    collisions: list[Collision] = []
    unknown = False

    if normalized_paths:
        git_state = worktree_state(root)
        if git_state == "REPOSITORY":
            try:
                for path in dirty_paths(root, normalized_paths):
                    collisions.append(
                        Collision("PATH", path, "git:worktree", "git:status")
                    )
            except ValueError:
                unknown = True
        elif git_state == "UNREACHABLE":
            # Hay un repositorio pero su estado no se pudo leer. Sin esta rama
            # la única fuente de evidencia desaparece en silencio y el veredicto
            # cae en `NONE`/`CONTINUE`, que es el más permisivo posible.
            unknown = True

    relevant_claim_bases: list[tuple[str, str, str]] = []
    claim_root = root / ".lifecycle" / "local" / "claims"
    if claim_root.is_dir():
        for claim_path in sorted(claim_root.glob("*.env")):
            try:
                claim = load_env(claim_path)
                if claim.get("STATUS", "ACTIVE") != "ACTIVE":
                    continue
                actor = claim.get("ACTOR", "UNKNOWN")
                source = claim_path.relative_to(root).as_posix()
                claim_is_relevant = False
                for claimed in _csv(claim.get("PATHS", "")):
                    if any(_paths_overlap(claimed, path) for path in normalized_paths):
                        collisions.append(Collision("PATH", claimed, actor, source))
                        claim_is_relevant = True
                for claimed in _csv(claim.get("SYMBOLS", "")):
                    if claimed in normalized_symbols:
                        collisions.append(Collision("SYMBOL", claimed, actor, source))
                        claim_is_relevant = True
                for claimed in _csv(claim.get("CONTRACTS", "")):
                    if claimed in normalized_contracts:
                        collisions.append(Collision("CONTRACT", claimed, actor, source))
                        claim_is_relevant = True
                for key, claimed_decision in _criteria(
                    _csv(claim.get("CRITERIA", ""))
                ).items():
                    if key not in normalized_criteria:
                        continue
                    proposed = normalized_criteria[key]
                    claim_is_relevant = True
                    if proposed == claimed_decision:
                        continue
                    subject = (
                        f"{key}={claimed_decision}->{proposed}"
                        if proposed and claimed_decision
                        else f"{key}={claimed_decision or 'UNKNOWN'}"
                    )
                    collisions.append(Collision("CRITERIA", subject, actor, source))
                if claim_is_relevant:
                    relevant_claim_bases.append(
                        (actor, claim.get("BASE_FINGERPRINT", ""), source)
                    )
            except (OSError, ValueError):
                unknown = True

    claim_mismatch, base_unknown, base_compared = _base_collisions(
        collisions,
        relevant_claim_bases,
        base_fingerprint=base_fingerprint,
    )
    unknown = unknown or base_unknown
    deduplicated = tuple(
        sorted(
            set(collisions),
            key=lambda item: (item.kind, item.subject, item.actor, item.source),
        )
    )
    kinds = {item.kind for item in deduplicated}
    conflicting_criteria = any(
        item.kind == "CRITERIA" and "->" in item.subject for item in deduplicated
    )
    if unknown:
        state = "FOUND" if deduplicated else "UNKNOWN"
        recommendation = "BLOCK"
    elif "BASE_MISMATCH" in kinds:
        state = "FOUND"
        recommendation = "BLOCK"
    elif conflicting_criteria:
        state = "FOUND"
        recommendation = "REPLAN"
    elif deduplicated:
        state = "FOUND"
        recommendation = "COORDINATE"
    else:
        state = "NONE"
        recommendation = "CONTINUE"
    return CollisionReport(
        state=state,
        paths=tuple(
            sorted({item.subject for item in deduplicated if item.kind == "PATH"})
        ),
        symbols=tuple(
            sorted({item.subject for item in deduplicated if item.kind == "SYMBOL"})
        ),
        contracts=tuple(
            sorted({item.subject for item in deduplicated if item.kind == "CONTRACT"})
        ),
        criteria=tuple(
            sorted({item.subject for item in deduplicated if item.kind == "CRITERIA"})
        ),
        actors=tuple(sorted({item.actor for item in deduplicated})),
        # `NO` solo cuando una comparación ocurrió de verdad; sin base
        # comparable el valor honesto es `UNKNOWN` (contrato del SKILL.md).
        # Este `UNKNOWN` informativo no alimenta la compuerta `unknown`: un
        # workspace sin claims sigue siendo NONE/CONTINUE.
        base_mismatch=(
            "YES"
            if claim_mismatch
            else ("UNKNOWN" if unknown or not base_compared else "NO")
        ),
        recommendation=recommendation,
        collisions=deduplicated,
    )


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = PurePosixPath(normalize_relative(left).as_posix()).parts
    right_parts = PurePosixPath(normalize_relative(right).as_posix()).parts
    shorter = min(len(left_parts), len(right_parts))
    return left_parts[:shorter] == right_parts[:shorter]


def _csv(raw: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in raw.split(",") if value.strip())


def _criteria(values: tuple[str, ...]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for value in values:
        key, separator, decision = value.strip().partition("=")
        key = key.strip()
        decision = decision.strip()
        if not key or any(character in key for character in "\r\n\0,"):
            raise ValueError(f"criterio inválido: {value!r}")
        if separator and any(character in decision for character in "\r\n\0,"):
            raise ValueError(f"criterio inválido: {value!r}")
        if key in normalized and normalized[key] != decision:
            raise ValueError(f"criterio duplicado: {key}")
        normalized[key] = decision
    return normalized


def _base_collisions(
    collisions: list[Collision],
    relevant_claim_bases: list[tuple[str, str, str]],
    *,
    base_fingerprint: str,
) -> tuple[bool, bool, bool]:
    unknown_values = {"", "UNKNOWN", "N/D", "NOT_APPLICABLE"}
    known = tuple(
        (actor, value, source)
        for actor, value, source in relevant_claim_bases
        if value.upper() not in unknown_values
    )
    has_unknown = len(known) != len(relevant_claim_bases)
    caller_base_known = bool(
        base_fingerprint and base_fingerprint.upper() not in unknown_values
    )
    # Hubo comparación real solo si existen bases de claims conocidas y algo
    # contra qué compararlas: la base del consultante o una segunda base.
    compared = bool(known) and (caller_base_known or len(known) > 1)
    distinct = {value for _, value, _ in known}
    mismatch = len(distinct) > 1
    if caller_base_known:
        mismatch = mismatch or any(value != base_fingerprint for _, value, _ in known)
    if mismatch:
        for actor, value, source in known:
            if len(distinct) > 1 or value != base_fingerprint:
                collisions.append(Collision("BASE_MISMATCH", value, actor, source))
    return mismatch, has_unknown, compared

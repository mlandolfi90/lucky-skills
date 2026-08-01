from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LocalObservation:
    result: str
    versioning: str
    fingerprint: str
    head: str
    branch: str
    dirty: bool
    dirty_count: int
    entry_count: int
    scan_status: str
    git_safe_override: bool


@dataclass(frozen=True)
class RemoteObservation:
    result: str
    state: str
    name: str = "NONE"
    url: str = "NONE"
    head: str = "UNKNOWN"
    ref: str = "UNKNOWN"
    source_id: str = "UNRESOLVED"
    redirect_policy: str = "DENY"
    query_attempted: bool = False
    candidates: tuple[str, ...] = field(default_factory=tuple)
    evidence_level: str = "UNKNOWN"


@dataclass(frozen=True)
class RuntimeObservation:
    result: str
    state: str
    version: str
    target: str
    source: str
    evidence_level: str


@dataclass(frozen=True)
class CapabilitiesObservation:
    result: str
    state: str
    fingerprint: str
    entries: tuple[str, ...]
    evidence_level: str

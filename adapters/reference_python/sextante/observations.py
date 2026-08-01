from __future__ import annotations

import hashlib

from .models import CapabilitiesObservation, RuntimeObservation


CAPABILITY_STATES = {
    "DETECTED",
    "LOADED",
    "INVOKABLE",
    "UNAVAILABLE",
    "UNKNOWN",
}
ALIGNING_EVIDENCE_LEVELS = {"VERIFIED_DIRECT", "HUMAN_PROVIDED"}
MAX_CAPABILITY_COUNT = 999


def normalize_runtime(
    *,
    requested_result: str,
    version: str,
    target: str,
    source: str,
    evidence_level: str,
    configured_mode: str,
) -> RuntimeObservation:
    if requested_result == "AUTO":
        if configured_mode == "NONE":
            return RuntimeObservation(
                result="PARTIAL",
                state="EVIDENCE_UNVERIFIED",
                version="UNKNOWN",
                target="UNKNOWN",
                source="SOURCES.env",
                evidence_level="DECLARED",
            )
        return RuntimeObservation(
            result="PARTIAL",
            state="UNDECLARED",
            version="UNKNOWN",
            target="UNKNOWN",
            source="NOT_PROVIDED",
            evidence_level="UNKNOWN",
        )
    missing_observation = evidence_level not in ALIGNING_EVIDENCE_LEVELS or not source
    missing_target = requested_result in {"ALIGNED", "DRIFT"} and not target
    if requested_result in {"ALIGNED", "DRIFT", "NOT_APPLICABLE"} and (
        missing_observation or missing_target
    ):
        return RuntimeObservation(
            result="PARTIAL",
            state="TARGET_MISSING" if missing_target else "EVIDENCE_MISSING",
            version=version or "UNKNOWN",
            target=target or "UNKNOWN",
            source=source or "NOT_PROVIDED",
            evidence_level=evidence_level,
        )
    state = "VERIFIED" if requested_result in {"ALIGNED", "DRIFT"} else requested_result
    return RuntimeObservation(
        result=requested_result,
        state=state,
        version=version or "UNKNOWN",
        target=(
            "NOT_APPLICABLE"
            if requested_result == "NOT_APPLICABLE"
            else (target or "UNKNOWN")
        ),
        source=source or "NOT_PROVIDED",
        evidence_level=evidence_level,
    )


def normalize_capabilities(
    raw_entries: list[str],
    *,
    evidence_level: str,
) -> CapabilitiesObservation:
    entries: list[str] = []
    has_unknown = False
    for raw_entry in raw_entries:
        parts = raw_entry.split("|")
        if len(parts) not in {3, 4}:
            raise ValueError(
                "capability debe usar KIND|NAME|STATE o KIND|NAME|STATE|VERSION"
            )
        kind, name, state = (part.strip() for part in parts[:3])
        version = parts[3].strip() if len(parts) == 4 else "UNKNOWN"
        state = state.upper()
        if not kind or not name or state not in CAPABILITY_STATES:
            raise ValueError(f"capability inválida: {raw_entry}")
        has_unknown = has_unknown or state == "UNKNOWN"
        entries.append(f"{kind}|{name}|{state}|{version or 'UNKNOWN'}")
    normalized = tuple(sorted(set(entries)))
    if len(normalized) > MAX_CAPABILITY_COUNT:
        raise ValueError(
            f"capability excede el máximo de {MAX_CAPABILITY_COUNT} entradas"
        )
    payload = "\n".join(normalized)
    fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    evidence_is_aligning = evidence_level in ALIGNING_EVIDENCE_LEVELS
    if not normalized or has_unknown or not evidence_is_aligning:
        result = "PARTIAL"
    else:
        result = "ALIGNED"
    return CapabilitiesObservation(
        result=result,
        state=(
            "NOT_PROVIDED"
            if not normalized
            else (
                "INCOMPLETE"
                if has_unknown
                else ("INVENTORIED" if evidence_is_aligning else "EVIDENCE_UNVERIFIED")
            )
        ),
        fingerprint=fingerprint,
        entries=normalized,
        evidence_level=evidence_level if normalized else "UNKNOWN",
    )

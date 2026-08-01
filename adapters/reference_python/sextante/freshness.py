from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone


def enforce_freshness(observation, observed_at: str, *, max_age_seconds: int):
    if observation.result not in {"ALIGNED", "DRIFT", "NOT_APPLICABLE"}:
        return observation
    observed = _parse_utc(observed_at)
    if observed is None:
        return replace(observation, result="PARTIAL", state="INVALID_TIMESTAMP")
    age_seconds = (datetime.now(timezone.utc) - observed).total_seconds()
    if age_seconds < -300 or age_seconds > max_age_seconds:
        return replace(observation, result="STALE", state="EVIDENCE_EXPIRED")
    return observation


def _parse_utc(value: str) -> datetime | None:
    if not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        return None
    return parsed

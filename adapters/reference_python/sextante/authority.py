from __future__ import annotations


MAX_ACTOR_LENGTH = 256


def is_actor(value: str) -> bool:
    return any(
        _has_actor_prefix(value, prefix)
        for prefix in ("session:", "agent:", "human:", "harness:")
    )


def is_human_actor(value: str) -> bool:
    return _has_actor_prefix(value, "human:")


def is_mother_session_actor(value: str) -> bool:
    normalized = value.lower()
    return normalized == "session:mother" or _has_actor_prefix(
        value,
        "session:mother:",
    )


def _has_actor_prefix(value: str, prefix: str) -> bool:
    return (
        value.lower().startswith(prefix)
        and bool(value[len(prefix) :].strip())
        and len(value) <= MAX_ACTOR_LENGTH
        and not any(character in value for character in "\r\n\0")
    )

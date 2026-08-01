from __future__ import annotations


SPECIAL_REMOTE_REFS = {"UNKNOWN", "NOT_APPLICABLE"}


def branch_to_ref(branch: str) -> str:
    if branch in {"DETACHED_OR_UNBORN", *SPECIAL_REMOTE_REFS}:
        return "UNKNOWN"
    candidate = f"refs/heads/{branch}"
    return candidate if valid_remote_ref(candidate) else "UNKNOWN"


def valid_remote_ref(value: str) -> bool:
    if value in SPECIAL_REMOTE_REFS:
        return True
    return (
        value.startswith("refs/heads/")
        and len(value) <= 1024
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
        and not any(character in value for character in " ~^:?*\\[")
        and ".." not in value
        and "@{" not in value
        and "//" not in value
        and not value.startswith("refs/heads/-")
        and not value.endswith(("/", ".", ".lock"))
    )

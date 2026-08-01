from __future__ import annotations


def validate_branch_prefix(value: str) -> str:
    if (
        not value
        or not value.endswith("/")
        or value.startswith(("/", "."))
        or ".." in value
        or any(character in value for character in " ~^:?*[\\\r\n\0")
    ):
        raise ValueError("branch_prefix inválido")
    return value


def release_branch(
    *,
    prefix: str,
    skill_id: str,
    skill_version: str,
    plan_hash: str,
) -> str:
    return (
        f"{validate_branch_prefix(prefix)}skills-{skill_id}-v{skill_version}-"
        f"{plan_hash[:8]}"
    )

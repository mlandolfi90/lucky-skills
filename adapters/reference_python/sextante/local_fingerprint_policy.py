from __future__ import annotations

import hashlib


MAX_STATE_MAP_NORMALIZATION_BYTES = 1_000_000
STATE_MAP_PATH = ".lifecycle/state/STATE-MAP.env"
_FINGERPRINT_PREFIX = b'GIT_LOCAL_FINGERPRINT="'
_FINGERPRINT_REPLACEMENT = b'GIT_LOCAL_FINGERPRINT="<EXCLUDED_SELF_VALUE>"'


def normalize_fingerprint_material(
    relative_path: str,
    content: bytes,
) -> tuple[bytes, bool]:
    """Remove only STATE-MAP's canonical self-fingerprint value."""
    if (
        relative_path != STATE_MAP_PATH
        or len(content) > MAX_STATE_MAP_NORMALIZATION_BYTES
    ):
        return content, False

    lines = content.splitlines(keepends=True)
    matching_indexes = [
        index for index, line in enumerate(lines) if _is_fingerprint_line(line)
    ]
    if len(matching_indexes) != 1:
        return content, False

    index = matching_indexes[0]
    _, ending = _line_and_ending(lines[index])
    normalized = list(lines)
    normalized[index] = _FINGERPRINT_REPLACEMENT + ending
    return b"".join(normalized), True


def git_blob_oid(content: bytes, object_format: str) -> str:
    sha1, sha256 = git_blob_oids(content)
    if object_format == "sha1":
        return sha1
    if object_format == "sha256":
        return sha256
    raise ValueError(f"formato de objeto Git no soportado: {object_format}")


def git_blob_oids(content: bytes) -> tuple[str, str]:
    header = f"blob {len(content)}\0".encode("ascii")
    sha1 = _sha1()
    sha1.update(header)
    sha1.update(content)
    sha256 = hashlib.sha256()
    sha256.update(header)
    sha256.update(content)
    return sha1.hexdigest(), sha256.hexdigest()


def _is_fingerprint_line(line: bytes) -> bool:
    body, _ = _line_and_ending(line)
    if not body.startswith(_FINGERPRINT_PREFIX) or not body.endswith(b'"'):
        return False
    value = body[len(_FINGERPRINT_PREFIX) : -1]
    return b'"' not in value and b"\0" not in value


def _line_and_ending(line: bytes) -> tuple[bytes, bytes]:
    for ending in (b"\r\n", b"\n", b"\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, b""


def _sha1():
    try:
        return hashlib.sha1(usedforsecurity=False)
    except TypeError:
        return hashlib.sha1()

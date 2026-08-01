from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable


FINGERPRINT_FORMAT = "SEXTANTE_LOCAL_V4"


def canonical_record(*fields: object) -> str:
    return json.dumps(
        [str(field) for field in fields],
        ensure_ascii=True,
        separators=(",", ":"),
    )


def fingerprint_records(records: Iterable[str]) -> str:
    material = "\n".join(records).encode("ascii")
    return hashlib.sha256(material).hexdigest()


def portable_path_text(value: str) -> bool:
    return "\ufffd" not in value and not any(
        0xD800 <= ord(character) <= 0xDFFF for character in value
    )

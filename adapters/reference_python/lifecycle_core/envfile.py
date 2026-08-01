"""Shared strict CLAVE=VALOR codec.

Sextante owns the hardened implementation in v3. Re-export it here so every
new adapter uses one parser and one atomic writer.
"""

from sextante.envfile import (
    KEY_PATTERN,
    canonical_env,
    load_env,
    load_env_document,
    parse_env,
    read_stable_utf8,
    write_immutable_atomic,
)

__all__ = [
    "KEY_PATTERN",
    "canonical_env",
    "load_env",
    "load_env_document",
    "parse_env",
    "read_stable_utf8",
    "write_immutable_atomic",
]

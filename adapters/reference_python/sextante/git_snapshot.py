from __future__ import annotations

from dataclasses import dataclass

from .file_fingerprint import BlobIdentity
from .fingerprint_contract import portable_path_text


@dataclass(frozen=True)
class IndexEntry:
    mode: str
    oid: str
    stage: int
    path: str


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    oid: str
    path: str


def parse_index(output: str) -> tuple[IndexEntry, ...]:
    entries: list[IndexEntry] = []
    for record in _records(output):
        metadata, separator, path = record.partition("\t")
        parts = metadata.split()
        if not separator or len(parts) != 3 or not parts[2].isdigit():
            raise ValueError("salida de índice Git inválida")
        entries.append(IndexEntry(parts[0], parts[1], int(parts[2]), path))
    return tuple(entries)


def parse_tree(output: str) -> tuple[TreeEntry, ...]:
    entries: list[TreeEntry] = []
    for record in _records(output):
        metadata, separator, path = record.partition("\t")
        parts = metadata.split()
        if not separator or len(parts) != 3:
            raise ValueError("salida de árbol Git inválida")
        mode, object_type, oid = parts
        if object_type not in {"blob", "commit"}:
            raise ValueError("tipo de objeto Git inesperado")
        entries.append(TreeEntry(mode, oid, path))
    return tuple(entries)


def dirty_paths(
    *,
    index: tuple[IndexEntry, ...],
    head_tree: tuple[TreeEntry, ...],
    untracked: tuple[str, ...],
    blobs: tuple[BlobIdentity, ...],
    object_format: str,
) -> set[str]:
    dirty = set(untracked)
    stage_zero = {entry.path: entry for entry in index if entry.stage == 0}
    tree = {entry.path: entry for entry in head_tree}
    observed = {blob.path: blob for blob in blobs}

    for entry in index:
        if entry.stage != 0:
            dirty.add(entry.path)
    for path in set(stage_zero) | set(tree):
        index_entry = stage_zero.get(path)
        tree_entry = tree.get(path)
        if (
            index_entry is None
            or tree_entry is None
            or index_entry.mode != tree_entry.mode
            or index_entry.oid != tree_entry.oid
        ):
            dirty.add(path)
    for path, entry in stage_zero.items():
        if entry.mode == "160000":
            continue
        blob = observed.get(path)
        # Contra el índice se compara el OID del contenido CANÓNICO, no el de
        # los bytes del disco: git guarda el contenido normalizado, así que con
        # `core.autocrlf` un archivo intacto en CRLF daba un OID crudo distinto
        # al del índice y salía sucio con `git status` limpio (mismo origen que
        # la huella no reproducible, local-fingerprint v2).
        observed_oid = (
            blob.material_sha256
            if blob and object_format == "sha256"
            else (blob.material_sha1 if blob else None)
        )
        if observed_oid != entry.oid:
            dirty.add(path)
        if blob and blob.mode != "UNOBSERVABLE" and blob.mode != entry.mode:
            dirty.add(path)
    return dirty


def _records(output: str) -> tuple[str, ...]:
    records = tuple(record for record in output.split("\0") if record)
    if any(not portable_path_text(record) for record in records):
        raise ValueError("salida Git contiene texto de ruta no portable")
    return records

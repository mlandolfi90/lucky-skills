from __future__ import annotations

import hashlib
import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .local_fingerprint_policy import (
    MAX_STATE_MAP_NORMALIZATION_BYTES,
    STATE_MAP_PATH,
    git_blob_oids,
    normalize_fingerprint_material,
)
from .fingerprint_contract import canonical_record, portable_path_text


MAX_TOTAL_CONTENT_BYTES = 512 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024
# Windows corta las rutas en 260 caracteres. Git las escribe igual (usa su
# propia API), así que el archivo EXISTE y nosotros no lo alcanzamos.
WINDOWS_PATH_LIMIT = 260


def _fuera_de_alcance(candidate: Path) -> bool:
    """¿El archivo no está, o no llegamos a él?

    Los dos casos levantan FileNotFoundError, así que el errno no los separa.
    Y separarlos importa: borrar un archivo trackeado es trabajo normal y no
    debe degradar nada, mientras que no alcanzarlo deja la huella incompleta
    sin que se note. Medido en vivo: un clon en ruta profunda dejó 10 archivos
    de 260-266 caracteres fuera del alcance y la huella salió distinta,
    declarándose COMPLETE y ALIGNED.
    """
    return os.name == "nt" and len(str(candidate)) >= WINDOWS_PATH_LIMIT


@dataclass(frozen=True)
class FingerprintResult:
    material: tuple[str, ...]
    blobs: tuple["BlobIdentity", ...]
    entry_count: int
    complete: bool
    status: str


@dataclass(frozen=True)
class FileHashResult:
    digest: str
    blob_sha1: str
    blob_sha256: str
    material_blob_sha1: str
    material_blob_sha256: str
    material_size: int
    material_normalized: bool
    bytes_read: int
    status: str


@dataclass(frozen=True)
class BlobIdentity:
    path: str
    sha1: str
    sha256: str
    material_sha1: str
    material_sha256: str
    mode: str


def fingerprint_files(
    workspace: Path,
    relative_paths: Iterable[str],
    *,
    max_entries: int,
    timeout_seconds: int,
) -> FingerprintResult:
    paths = tuple(sorted(set(relative_paths)))
    if len(paths) > max_entries:
        paths = paths[:max_entries]
        initial_status = "ENTRY_LIMIT_REACHED"
    else:
        initial_status = "COMPLETE"

    material: list[str] = []
    blobs: list[BlobIdentity] = []
    remaining_bytes = MAX_TOTAL_CONTENT_BYTES
    deadline = time.monotonic() + timeout_seconds
    status_value = initial_status

    for raw_path in paths:
        if time.monotonic() > deadline:
            status_value = "TIME_LIMIT_REACHED"
            break
        relative_path = Path(raw_path)
        if not portable_path_text(raw_path):
            material.append(canonical_record("ENTRY", "UNSUPPORTED_PATH_TEXT"))
            status_value = "UNSUPPORTED_PATH_TEXT"
            continue
        if (
            relative_path.is_absolute()
            or relative_path.drive
            or ".." in relative_path.parts
        ):
            material.append(canonical_record("ENTRY", raw_path, "UNSAFE_PATH"))
            status_value = "UNSAFE_PATH"
            continue
        candidate = workspace / relative_path
        try:
            metadata = candidate.lstat()
        except OSError:
            material.append(
                canonical_record("ENTRY", relative_path.as_posix(), "MISSING")
            )
            if _fuera_de_alcance(candidate):
                status_value = "PATH_LIMIT_REACHED"
            continue

        if stat.S_ISLNK(metadata.st_mode):
            try:
                link_target = os.readlink(candidate)
            except OSError:
                link_target = "UNREADABLE"
                status_value = "UNREADABLE_ENTRY"
            if not portable_path_text(link_target):
                material.append(
                    canonical_record(
                        "ENTRY",
                        relative_path.as_posix(),
                        "UNSUPPORTED_PATH_TEXT",
                    )
                )
                status_value = "UNSUPPORTED_PATH_TEXT"
                continue
            link_hash = hashlib.sha256(
                link_target.encode("utf-8", errors="surrogatepass")
            ).hexdigest()
            link_bytes = os.fsencode(link_target)
            blob_sha1, blob_sha256 = _blob_oids(link_bytes)
            blobs.append(
                BlobIdentity(
                    path=relative_path.as_posix(),
                    sha1=blob_sha1,
                    sha256=blob_sha256,
                    material_sha1=blob_sha1,
                    material_sha256=blob_sha256,
                    mode="120000",
                )
            )
            material.append(
                canonical_record(
                    "ENTRY",
                    relative_path.as_posix(),
                    "SYMLINK",
                    link_hash,
                )
            )
            continue
        if not stat.S_ISREG(metadata.st_mode):
            material.append(
                canonical_record(
                    "ENTRY",
                    relative_path.as_posix(),
                    "SPECIAL",
                    stat.S_IFMT(metadata.st_mode),
                )
            )
            status_value = "SPECIAL_ENTRY"
            continue
        if metadata.st_size > remaining_bytes:
            material.append(
                canonical_record(
                    "ENTRY",
                    relative_path.as_posix(),
                    "CONTENT_LIMIT",
                    metadata.st_size,
                )
            )
            status_value = "CONTENT_LIMIT_REACHED"
            continue

        hashed = _hash_file(
            candidate,
            relative_path=relative_path.as_posix(),
            expected=metadata,
            deadline=deadline,
            byte_limit=remaining_bytes,
        )
        if hashed.status != "COMPLETE":
            material.append(
                canonical_record(
                    "ENTRY",
                    relative_path.as_posix(),
                    hashed.status,
                    metadata.st_size,
                )
            )
            status_value = hashed.status
            if hashed.status == "TIME_LIMIT_REACHED":
                break
            continue
        remaining_bytes -= hashed.bytes_read
        observed_mode = _working_tree_mode(metadata.st_mode)
        # El modo no entra en la huella (D-078): un mismo árbol debe producir la
        # misma huella en Windows y Linux, trackeado o no. El gate de permisos
        # vive en dirty, que sí usa el modo observado del blob.
        # El registro describe el contenido CANÓNICO y nada del transporte: ni
        # el tamaño en disco ni si hubo conversión de finales de línea entran
        # acá. Si entraran, dos checkouts del mismo commit —uno con CRLF, otro
        # con LF— emitirían registros distintos con el mismo digest, y la
        # huella volvería a no reproducir (exactamente lo que pasó al primer
        # intento del arreglo).
        material.append(
            canonical_record(
                "ENTRY",
                relative_path.as_posix(),
                "FILE",
                hashed.material_size,
                "NORMALIZED_SELF_VALUE" if hashed.material_normalized else "CANONICAL",
                hashed.digest,
            )
        )
        blobs.append(
            BlobIdentity(
                path=relative_path.as_posix(),
                sha1=hashed.blob_sha1,
                sha256=hashed.blob_sha256,
                material_sha1=hashed.material_blob_sha1,
                material_sha256=hashed.material_blob_sha256,
                mode=observed_mode,
            )
        )

    complete = status_value == "COMPLETE"
    return FingerprintResult(
        material=tuple(material),
        blobs=tuple(blobs),
        entry_count=len(material),
        complete=complete,
        status=status_value,
    )


BINARY_SNIFF_BYTES = 8000


class _EolNormalizer:
    """Convierte CRLF a LF en streaming, salvo que el contenido sea binario.

    Por qué (local-fingerprint v2, caso Lucky-PizarraEvo 2026-08-03): la
    huella hasheaba los BYTES DEL CHECKOUT. Con `core.autocrlf` git reescribe
    los finales de línea al bajar los archivos, así que el mismo commit daba
    huellas distintas según la máquina y según qué herramienta escribió cada
    archivo — y el STATE-MAP, que se versiona y viaja a cada destino, llevaba
    adentro un valor específico de un checkout. Un clon del mismo commit nunca
    reproducía la huella sellada, y `revalidar` no convergía jamás.

    Git guarda LF en el repositorio, así que normalizar a LF devuelve el mismo
    contenido que git almacena: la huella pasa a describir el CONTENIDO
    VERSIONADO y no el transporte de bytes. La decisión binario/texto imita a
    git: NUL en los primeros 8000 bytes ⇒ binario, y ahí no se toca nada.
    """

    def __init__(self) -> None:
        self._decided = False
        self.binary = False
        self._sniffed = 0
        self._pending_cr = False

    def feed(self, chunk: bytes) -> bytes:
        if not self._decided and self._sniffed < BINARY_SNIFF_BYTES:
            ventana = chunk[: BINARY_SNIFF_BYTES - self._sniffed]
            self._sniffed += len(ventana)
            if b"\0" in ventana:
                self.binary = True
                self._decided = True
            elif self._sniffed >= BINARY_SNIFF_BYTES:
                self._decided = True
        if self.binary:
            return chunk
        if self._pending_cr:
            # Un CR que quedó colgando del chunk anterior: era CRLF sólo si
            # este arranca con LF; si no, es un CR suelto y git no lo toca.
            chunk = b"\r" + chunk
            self._pending_cr = False
        if chunk.endswith(b"\r"):
            self._pending_cr = True
            chunk = chunk[:-1]
        return chunk.replace(b"\r\n", b"\n")

    def finish(self) -> bytes:
        if self._pending_cr and not self.binary:
            self._pending_cr = False
            return b"\r"
        return b""


def _hash_file(
    path: Path,
    *,
    relative_path: str,
    expected: os.stat_result,
    deadline: float,
    byte_limit: int,
) -> FileHashResult:
    digest = hashlib.sha256()
    blob_sha1 = _sha1()
    blob_sha256 = hashlib.sha256()
    header = f"blob {expected.st_size}\0".encode("ascii")
    blob_sha1.update(header)
    blob_sha256.update(header)
    normalizer = _EolNormalizer()
    canonical: list[bytes] = []
    canonical_size = 0
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    bytes_read = 0
    state_map_chunks: list[bytes] | None = (
        []
        if relative_path == STATE_MAP_PATH
        and expected.st_size <= MAX_STATE_MAP_NORMALIZATION_BYTES
        else None
    )
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file(expected, opened):
            return _failed_hash("CHANGED_DURING_SCAN")
        while True:
            if time.monotonic() > deadline:
                return _failed_hash("TIME_LIMIT_REACHED", bytes_read=bytes_read)
            chunk = os.read(descriptor, min(CHUNK_BYTES, byte_limit - bytes_read + 1))
            if not chunk:
                break
            bytes_read += len(chunk)
            if bytes_read > byte_limit:
                return _failed_hash("CONTENT_LIMIT_REACHED", bytes_read=bytes_read)
            blob_sha1.update(chunk)
            blob_sha256.update(chunk)
            normalizado = normalizer.feed(chunk)
            if normalizado:
                canonical.append(normalizado)
                canonical_size += len(normalizado)
            if state_map_chunks is not None:
                state_map_chunks.append(chunk)
        cola = normalizer.finish()
        if cola:
            canonical.append(cola)
            canonical_size += len(cola)
        finished = os.fstat(descriptor)
        if not _same_file(opened, finished) or bytes_read != finished.st_size:
            return _failed_hash("CHANGED_DURING_SCAN", bytes_read=bytes_read)
    except (OSError, ValueError):
        return _failed_hash("UNREADABLE_ENTRY", bytes_read=bytes_read)
    finally:
        if descriptor is not None:
            os.close(descriptor)

    # El material de la huella es el contenido CANÓNICO (LF), no los bytes del
    # checkout: así un clon del mismo commit reproduce la huella. Los blob OIDs
    # crudos siguen disponibles aparte para quien necesite los bytes en disco.
    contenido_canonico = b"".join(canonical)
    digest.update(contenido_canonico)
    material_digest = digest.hexdigest()
    material_blob_sha1, material_blob_sha256 = git_blob_oids(contenido_canonico)
    material_size = canonical_size
    # `material_normalized` marca SOLO la exclusión autorreferencial del
    # STATE-MAP, que es una decisión de contenido y debe verse en el registro.
    # La conversión de finales de línea es transporte: no se marca.
    material_normalized = False
    if state_map_chunks is not None:
        # El STATE-MAP además excluye su propio valor de huella (autorreferencia),
        # y lo hace sobre el contenido canónico, no sobre los bytes del disco.
        normalized, excluded = normalize_fingerprint_material(
            relative_path,
            contenido_canonico,
        )
        if excluded:
            # Solo el material de la HUELLA lleva la exclusión. Los blob OIDs
            # se comparan contra el índice de git para decidir `dirty`, y el
            # índice tiene el contenido real: si les metiéramos la exclusión,
            # el STATE-MAP saldría sucio siempre, con el árbol limpio.
            material_digest = hashlib.sha256(normalized).hexdigest()
            material_size = len(normalized)
            material_normalized = True

    return FileHashResult(
        digest=material_digest,
        blob_sha1=blob_sha1.hexdigest(),
        blob_sha256=blob_sha256.hexdigest(),
        material_blob_sha1=material_blob_sha1,
        material_blob_sha256=material_blob_sha256,
        material_size=material_size,
        material_normalized=material_normalized,
        bytes_read=bytes_read,
        status="COMPLETE",
    )


def _blob_oids(content: bytes) -> tuple[str, str]:
    return git_blob_oids(content)


def _failed_hash(status: str, *, bytes_read: int = 0) -> FileHashResult:
    return FileHashResult(
        digest="",
        blob_sha1="",
        blob_sha256="",
        material_blob_sha1="",
        material_blob_sha256="",
        material_size=0,
        material_normalized=False,
        bytes_read=bytes_read,
        status=status,
    )


def _working_tree_mode(mode: int) -> str:
    if os.name == "nt":
        return "UNOBSERVABLE"
    return "100755" if mode & stat.S_IXUSR else "100644"


def _sha1():
    try:
        return hashlib.sha1(usedforsecurity=False)
    except TypeError:
        return hashlib.sha1()


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_mode == right.st_mode
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )

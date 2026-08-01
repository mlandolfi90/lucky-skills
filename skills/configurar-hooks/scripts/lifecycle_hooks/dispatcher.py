from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .contracts import HookEvent
from .runtime_io import read_stable_utf8, utc_now, write_immutable_atomic


RESULT_SCHEMA = "lifecycle.hook-result.v1"
MAX_RECEIPT_BYTES = 64 * 1024
OBSERVATIONS = {
    "SESSION_START": "Corroborar el estado con Sextante antes de asumir contexto.",
    "BEFORE_WRITE": "Confirmar TARGET y revisar colisiones antes de escribir.",
    "AFTER_WRITE": "Verificar el cambio pequeño y registrar su resultado.",
    "BEFORE_PUSH": "Confirmar alcance y autorización humana antes del push.",
    "AFTER_FAILURE": "Corregir primero; registrar la autopsia después.",
    "SESSION_END": "Sintetizar estado, pendientes y cierre antes de salir.",
}


def _canonical_json(values: Mapping[str, object]) -> str:
    return json.dumps(
        values,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sha256(values: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(values).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DispatchResult:
    event: str
    event_id: str
    harness: str
    workspace_id: str
    status: str
    observations: tuple[str, ...]
    receipt: str
    observed_at: str
    event_fingerprint: str
    mode: str = "ADVISORY"
    allow: bool = True
    schema: str = RESULT_SCHEMA

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "event": self.event,
            "event_id": self.event_id,
            "harness": self.harness,
            "workspace_id": self.workspace_id,
            "mode": self.mode,
            "status": self.status,
            "allow": self.allow,
            "observations": list(self.observations),
            "receipt": self.receipt,
            "observed_at": self.observed_at,
            "event_fingerprint": self.event_fingerprint,
        }


def dispatch_event(
    event: HookEvent,
    *,
    receipt_root: Path,
    enabled: bool = True,
) -> DispatchResult:
    event.validate()
    fingerprint = _sha256(event.to_mapping())
    if not enabled:
        return DispatchResult(
            event=event.event,
            event_id=event.event_id,
            harness=event.harness,
            workspace_id=event.workspace_id,
            status="DISABLED",
            observations=(),
            receipt="",
            observed_at="",
            event_fingerprint=fingerprint,
        )

    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_root / _receipt_name(event)
    if receipt_path.exists():
        return _load_matching_receipt(receipt_path, fingerprint)

    result = DispatchResult(
        event=event.event,
        event_id=event.event_id,
        harness=event.harness,
        workspace_id=event.workspace_id,
        status="OBSERVED",
        observations=(OBSERVATIONS[event.event],),
        receipt=str(receipt_path.resolve()),
        observed_at=utc_now(),
        event_fingerprint=fingerprint,
    )
    payload = result.to_mapping()
    payload["result_hash"] = _sha256(payload)
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        write_immutable_atomic(receipt_path, content)
    except ValueError:
        return _load_matching_receipt(receipt_path, fingerprint)
    return result


def verify_hook_receipt(path: Path) -> bool:
    try:
        payload = _load_json_object(path)
        result_hash = payload.pop("result_hash")
    except (KeyError, OSError, ValueError):
        return False
    return isinstance(result_hash, str) and result_hash == _sha256(payload)


def _receipt_name(event: HookEvent) -> str:
    identity = f"{event.harness}\0{event.event_id}".encode("utf-8")
    suffix = hashlib.sha256(identity).hexdigest()[:24]
    return f"hook-{suffix}.json"


def _load_matching_receipt(
    path: Path,
    expected_fingerprint: str,
) -> DispatchResult:
    payload = _load_json_object(path)
    result_hash = payload.pop("result_hash", None)
    if not isinstance(result_hash, str) or result_hash != _sha256(payload):
        raise ValueError("comprobante de hook inválido")
    if payload.get("event_fingerprint") != expected_fingerprint:
        raise ValueError("event_id reutilizado para un evento diferente")
    observations = payload.get("observations")
    if not isinstance(observations, list) or not all(
        isinstance(item, str) for item in observations
    ):
        raise ValueError("observaciones inválidas")
    return DispatchResult(
        schema=_required_text(payload, "schema"),
        event=_required_text(payload, "event"),
        event_id=_required_text(payload, "event_id"),
        harness=_required_text(payload, "harness"),
        workspace_id=_required_text(payload, "workspace_id"),
        mode=_required_text(payload, "mode"),
        status=_required_text(payload, "status"),
        allow=_required_bool(payload, "allow"),
        observations=tuple(observations),
        receipt=_required_text(payload, "receipt"),
        observed_at=_required_text(payload, "observed_at"),
        event_fingerprint=_required_text(payload, "event_fingerprint"),
    )


def _load_json_object(path: Path) -> dict[str, object]:
    raw = read_stable_utf8(path, max_bytes=MAX_RECEIPT_BYTES)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("JSON de comprobante inválido") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("comprobante debe ser un objeto JSON")
    return value


def _required_text(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} inválido")
    return value


def _required_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} inválido")
    return value

"""Contrato común de eventos lifecycle."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


EVENT_SCHEMA = "lifecycle.hook-event.v1"
COMMON_EVENTS = (
    "SESSION_START",
    "BEFORE_WRITE",
    "AFTER_WRITE",
    "BEFORE_PUSH",
    "AFTER_FAILURE",
    "SESSION_END",
)
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
WORKSPACE_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVENT_KEYS = frozenset(
    {
        "schema",
        "event",
        "event_id",
        "harness",
        "workspace_id",
    }
)


@dataclass(frozen=True)
class HookEvent:
    event: str
    event_id: str
    harness: str
    workspace_id: str
    schema: str = EVENT_SCHEMA

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> HookEvent:
        unknown = set(values) - EVENT_KEYS
        missing = EVENT_KEYS - set(values)
        if unknown:
            raise ValueError(f"campos no permitidos: {','.join(sorted(unknown))}")
        if missing:
            raise ValueError(f"faltan campos: {','.join(sorted(missing))}")
        if any(not isinstance(values[key], str) for key in EVENT_KEYS):
            raise ValueError("todos los campos del evento deben ser texto")

        event = cls(
            schema=str(values["schema"]),
            event=str(values["event"]),
            event_id=str(values["event_id"]),
            harness=str(values["harness"]),
            workspace_id=str(values["workspace_id"]),
        )
        event.validate()
        return event

    def validate(self) -> None:
        if self.schema != EVENT_SCHEMA:
            raise ValueError("schema de evento no soportado")
        if self.event not in COMMON_EVENTS:
            raise ValueError("evento común no soportado")
        if not IDENTIFIER_PATTERN.fullmatch(self.event_id):
            raise ValueError("event_id inválido")
        if not IDENTIFIER_PATTERN.fullmatch(self.harness):
            raise ValueError("harness inválido")
        if not WORKSPACE_ID_PATTERN.fullmatch(self.workspace_id):
            raise ValueError("workspace_id inválido")

    def to_mapping(self) -> dict[str, str]:
        self.validate()
        return {
            "schema": self.schema,
            "event": self.event,
            "event_id": self.event_id,
            "harness": self.harness,
            "workspace_id": self.workspace_id,
        }

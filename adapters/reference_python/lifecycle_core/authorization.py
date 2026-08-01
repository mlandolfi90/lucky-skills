from __future__ import annotations

from dataclasses import dataclass

from sextante.authority import is_human_actor


@dataclass(frozen=True)
class Authorization:
    actor: str
    target: str
    action: str
    plan_hash: str = ""

    def validate(self, *, expected_target: str, expected_action: str) -> None:
        if not is_human_actor(self.actor):
            raise ValueError("la autorización debe pertenecer a un actor human:")
        if self.target != expected_target:
            raise ValueError("el TARGET autorizado no coincide")
        if self.action != expected_action:
            raise ValueError("la acción autorizada no coincide")


def require_human(actor: str, *, field: str = "actor") -> str:
    if not is_human_actor(actor):
        raise ValueError(f"{field} debe identificar un actor human:")
    return actor

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PlanItem:
    skill_id: str
    role: str
    source: str
    destination: str
    action: str
    source_hash: str
    current_hash: str
    # Archivos preexistentes bajo `destination` sin equivalente en la fuente:
    # un `ARCHIVE_REPLACE` los elimina del árbol activo. Enumerarlos acá hace
    # que la baja quede dentro del PLAN_HASH que el humano confirma (D-041,
    # D-052); sin esto la compuerta mostraba menos de lo que la operación hacía.
    removes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdoptionPlan:
    source_skill: str
    target: str
    skill_id: str
    skill_version: str
    harness: str
    landing_receipt: str
    target_fingerprint: str
    dependencies: tuple[str, ...]
    items: tuple[PlanItem, ...]
    collisions: tuple[str, ...]
    risks: tuple[str, ...]
    plan_hash: str = ""

    @property
    def adoption_id(self) -> str:
        return f"adoption-{self.plan_hash[:16]}"

    @property
    def has_writes(self) -> bool:
        return any(item.action != "UNCHANGED" for item in self.items)

    def with_hash(self) -> AdoptionPlan:
        return replace(self, plan_hash=self.compute_hash())

    def compute_hash(self) -> str:
        payload = self.to_dict()
        payload["plan_hash"] = ""
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def from_json(cls, raw: str) -> AdoptionPlan:
        values = json.loads(raw)
        values["dependencies"] = tuple(values["dependencies"])
        values["items"] = tuple(
            PlanItem(**{**item, "removes": tuple(item.get("removes", ()))})
            for item in values["items"]
        )
        values["collisions"] = tuple(values["collisions"])
        values["risks"] = tuple(values["risks"])
        plan = cls(**values)
        if not plan.plan_hash or plan.plan_hash != plan.compute_hash():
            raise ValueError("PLAN_HASH inválido")
        return plan

    @classmethod
    def load(cls, path: Path) -> AdoptionPlan:
        return cls.from_json(path.read_text(encoding="utf-8"))

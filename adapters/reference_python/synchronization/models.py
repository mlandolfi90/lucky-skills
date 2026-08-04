from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepositoryAssessment:
    repo_id: str
    remote_url: str
    default_branch: str
    harness: str
    remote_head: str
    observed_version: str
    classification: str
    reason: str
    transition_hash: str
    changes: tuple[str, ...]
    risks: tuple[str, ...]
    collisions: tuple[str, ...]
    # Mensaje crudo de la falla cuando no se pudo medir. `reason` queda como
    # token estable para decidir; `detail` es para que un humano entienda QUÉ
    # falló sin volver a correr nada. Vacío cuando la medición sí se logró.
    detail: str = ""


@dataclass(frozen=True)
class SyncPlan:
    catalog: str
    registry: str
    skill_id: str
    skill_version: str
    branch_prefix: str
    source_hash: str
    repositories: tuple[RepositoryAssessment, ...]
    plan_hash: str = ""

    def with_hash(self) -> SyncPlan:
        return replace(self, plan_hash=self.compute_hash())

    def compute_hash(self) -> str:
        values = self.to_dict()
        values["plan_hash"] = ""
        payload = json.dumps(
            values,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

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
    def from_json(cls, raw: str) -> SyncPlan:
        values = json.loads(raw)
        values["repositories"] = tuple(
            RepositoryAssessment(
                **{
                    **item,
                    "changes": tuple(item["changes"]),
                    "risks": tuple(item["risks"]),
                    "collisions": tuple(item["collisions"]),
                }
            )
            for item in values["repositories"]
        )
        plan = cls(**values)
        if not plan.plan_hash or plan.plan_hash != plan.compute_hash():
            raise ValueError("BATCH_PLAN inválido")
        return plan

    @classmethod
    def load(cls, path: Path) -> SyncPlan:
        return cls.from_json(path.read_text(encoding="utf-8"))

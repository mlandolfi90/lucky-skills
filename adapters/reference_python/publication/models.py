from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleasePlan:
    catalog: str
    skill_id: str
    from_version: str
    to_version: str
    impact: str
    source_hash: str
    closure_receipt: str
    closure_hash: str
    canary_hash: str
    quality: str
    plan_hash: str = ""

    def with_hash(self) -> ReleasePlan:
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
    def from_json(cls, raw: str) -> ReleasePlan:
        plan = cls(**json.loads(raw))
        if not plan.plan_hash or plan.plan_hash != plan.compute_hash():
            raise ValueError("PLAN_HASH inválido")
        return plan

    @classmethod
    def load(cls, path: Path) -> ReleasePlan:
        return cls.from_json(path.read_text(encoding="utf-8"))

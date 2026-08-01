from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lifecycle_core.envfile import load_env

from lifecycle_core.receipts import local_state_root

from .models import AdoptionPlan
from .planner import build_plan
from .transaction import apply_plan, revalidate_state_map


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adopción atómica de Skills v3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--source-skill", required=True)
    plan.add_argument("--target", required=True)
    plan.add_argument(
        "--harness",
        required=True,
        choices=("generic", "claude-code", "claude-ai", "codex"),
    )
    plan.add_argument("--sextante-receipt", required=True)
    plan.add_argument("--legacy-path", action="append", default=[])
    plan.add_argument("--plan-out", default="")

    apply = subparsers.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm-plan-hash", required=True)
    apply.add_argument("--confirmed-by", required=True)
    apply.add_argument("--accept-risk-by", default="")
    apply.add_argument("--commit", action="store_true")
    apply.add_argument("--commit-confirmed-by", default="")
    revalidar = subparsers.add_parser("revalidar")
    revalidar.add_argument("--target", required=True)
    revalidar.add_argument("--confirmed-by", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "plan":
            return _plan(arguments)
        if arguments.command == "revalidar":
            return _revalidar(arguments)
        return _apply(arguments)
    except (OSError, ValueError) as error:
        print(f"ADOPTION_ERROR={error}", file=sys.stderr)
        print(f"ERROR_KIND={type(error).__name__}", file=sys.stderr)
        for note in getattr(error, "__notes__", ()):
            print(f"ADOPTION_INFO={note}", file=sys.stderr)
        return 1


def _plan(arguments: argparse.Namespace) -> int:
    plan = build_plan(
        source_skill=Path(arguments.source_skill),
        target=Path(arguments.target),
        harness=arguments.harness,
        landing_receipt=Path(arguments.sextante_receipt),
        legacy_paths=tuple(arguments.legacy_path),
    )
    output = (
        Path(arguments.plan_out)
        if arguments.plan_out
        else local_state_root("adopcion") / "plans" / f"{plan.plan_hash}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.read_text(encoding="utf-8") != plan.to_json():
        raise ValueError(f"colisión de plan: {output}")
    output.write_text(plan.to_json(), encoding="utf-8", newline="\n")
    actions = sorted({item.action for item in plan.items if item.action != "UNCHANGED"})
    print(f"SOURCE={plan.source_skill}")
    print(f"SKILL={plan.skill_id}@{plan.skill_version}")
    print(f"TARGET={plan.target}")
    print(f"HARNESS={plan.harness}")
    print(f"ACTION={','.join(actions) or 'NONE'}")
    print(f"COLLISIONS={len(plan.collisions)}")
    removes = tuple(
        f"{item.destination}/{path}" for item in plan.items for path in item.removes
    )
    print(f"REMOVES={len(removes)}")
    for removed in removes:
        print(f"REMOVE={removed}")
    print("COMMIT=NO")
    print(f"PLAN_HASH={plan.plan_hash}")
    print("WRITE_GATE=BLOCK")
    print("NEEDS=CONFIRM_ADOPTION")
    print(f"PLAN={output.resolve()}")
    return 0


def _revalidar(arguments: argparse.Namespace) -> int:
    receipt = revalidate_state_map(
        Path(arguments.target),
        confirmed_by=arguments.confirmed_by,
    )
    values = load_env(receipt)
    print("STATE_MAP=REVALIDATED")
    print(f"COMMIT={values['PREVIOUS_COMMIT'][:8]}->{values['NEW_COMMIT'][:8]}")
    print(
        "FINGERPRINT="
        f"{values['PREVIOUS_FINGERPRINT'][:8]}->{values['NEW_FINGERPRINT'][:8]}"
    )
    print(f"STATE_REVISION={values['STATE_REVISION']}")
    print(f"RECEIPT={receipt.resolve()}")
    return 0


def _apply(arguments: argparse.Namespace) -> int:
    saved = AdoptionPlan.load(Path(arguments.plan))
    current = build_plan(
        source_skill=Path(saved.source_skill),
        target=Path(saved.target),
        harness=saved.harness,
        landing_receipt=Path(saved.landing_receipt),
        legacy_paths=tuple(
            item.destination for item in saved.items if item.role == "LEGACY"
        ),
    )
    if current.plan_hash != saved.plan_hash:
        raise ValueError("el estado cambió; recalcular y reconfirmar el plan")
    receipt = apply_plan(
        current,
        confirmed_plan_hash=arguments.confirm_plan_hash,
        confirmed_by=arguments.confirmed_by,
        accept_risk_by=arguments.accept_risk_by,
        create_commit=arguments.commit,
        commit_confirmed_by=arguments.commit_confirmed_by,
    )
    print(f"ADOPTION={current.adoption_id}")
    print("RESULT=ADOPTED" if current.has_writes else "RESULT=ALREADY_ADOPTED")
    print("WRITE_GATE=PASS")
    values = load_env(receipt)
    print(f"VCS_VISIBLE={values.get('VCS_VISIBLE', 'UNKNOWN')}")
    ignored = values.get("VCS_IGNORED", "NONE")
    if ignored not in {"NONE", "NOT_APPLICABLE"}:
        print("WARNING=el .gitignore del proyecto oculta parte de la gobernanza")
        for path in ignored.split(","):
            print(f"VCS_IGNORED={path}")
    print(f"RECEIPT={receipt.resolve()}")
    return 0

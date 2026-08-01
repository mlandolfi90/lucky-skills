from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lifecycle_core.envfile import load_env

from .models import ReleasePlan
from .publisher import apply_release, build_release_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publicar una skill Skills v3")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--catalog", required=True)
    plan.add_argument("--skill", required=True)
    plan.add_argument(
        "--impact", choices=("PATCH", "MINOR", "MAJOR", "AUTO"), required=True
    )
    plan.add_argument("--closure-receipt", required=True)
    plan.add_argument("--output", required=True)

    apply = commands.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm-plan-hash", required=True)
    apply.add_argument("--confirmed-by", required=True)
    apply.add_argument("--commit", action="store_true")
    apply.add_argument("--commit-confirmed-by", default="")
    apply.add_argument("--tag", action="store_true")
    apply.add_argument("--tag-confirmed-by", default="")
    apply.add_argument("--push", action="store_true")
    apply.add_argument("--push-confirmed-by", default="")
    apply.add_argument("--remote", default="origin")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "plan":
            release = build_release_plan(
                catalog=Path(arguments.catalog),
                skill_id=arguments.skill,
                impact=arguments.impact,
                closure_receipt=Path(arguments.closure_receipt),
            )
            output = Path(arguments.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(release.to_json(), encoding="utf-8", newline="\n")
            print(f"SKILL={release.skill_id}")
            print(f"FROM_VERSION={release.from_version}")
            print(f"TO_VERSION={release.to_version}")
            print(f"IMPACT={release.impact}")
            print(f"QUALITY={release.quality}")
            print(f"CANARY_HASH={release.canary_hash}")
            print(f"PLAN_HASH={release.plan_hash}")
            print("WRITE_GATE=BLOCK")
            print("NEEDS=CONFIRM_RELEASE")
            return 0
        release = ReleasePlan.load(Path(arguments.plan))
        receipt = apply_release(
            release,
            confirmed_plan_hash=arguments.confirm_plan_hash,
            confirmed_by=arguments.confirmed_by,
            create_commit=arguments.commit,
            commit_confirmed_by=arguments.commit_confirmed_by,
            create_tag=arguments.tag,
            tag_confirmed_by=arguments.tag_confirmed_by,
            push=arguments.push,
            push_confirmed_by=arguments.push_confirmed_by,
            remote=arguments.remote,
        )
        values = load_env(receipt)
        for key in (
            "SKILL_ID",
            "FROM_VERSION",
            "TO_VERSION",
            "QUALITY",
            "COMMIT",
            "TAG",
            "PUSH",
            "RELEASE",
        ):
            print(f"{key}={values[key]}")
        print(f"RECEIPT={receipt.resolve()}")
        return 0
    except (OSError, ValueError) as error:
        print(f"PUBLICATION_ERROR={error}", file=sys.stderr)
        return 1

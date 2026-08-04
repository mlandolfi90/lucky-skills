from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lifecycle_core.envfile import load_env

from .branches import release_branch
from .models import SyncPlan
from .scanner import APPLICABLE, CLASSIFICATIONS, build_sync_plan
from .transaction import apply_sync_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sincronizar Skills v3")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--catalog", required=True)
    plan.add_argument("--registry", required=True)
    plan.add_argument("--skill", required=True)
    plan.add_argument("--confirmed-by", required=True)
    plan.add_argument("--branch-prefix", default="codex/")
    plan.add_argument("--output", required=True)

    apply = commands.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm-plan-hash", required=True)
    apply.add_argument("--repo", action="append", required=True)
    apply.add_argument("--confirmed-by", required=True)
    apply.add_argument("--push-confirmed-by", required=True)
    apply.add_argument("--git-author-name", required=True)
    apply.add_argument("--git-author-email", required=True)
    apply.add_argument("--accept-risks-by", default="")
    apply.add_argument("--accept-adaptation-by", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "plan":
            plan = build_sync_plan(
                catalog=Path(arguments.catalog),
                registry=Path(arguments.registry),
                skill_id=arguments.skill,
                confirmed_by=arguments.confirmed_by,
                branch_prefix=arguments.branch_prefix,
            )
            output = Path(arguments.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(plan.to_json(), encoding="utf-8", newline="\n")
            print(f"SKILL={plan.skill_id}@{plan.skill_version}")
            print(f"REPOSITORIES={len(plan.repositories)}")
            for classification in sorted(CLASSIFICATIONS):
                count = sum(
                    item.classification == classification for item in plan.repositories
                )
                print(f"{classification}={count}")
            print(f"BATCH_PLAN={plan.plan_hash}")
            print(f"BRANCH_PREFIX={plan.branch_prefix}")
            # Lo que no se pudo medir se nombra acá, con su causa. Si sólo
            # apareciera el conteo, un UNDETERMINED se leería como un repo
            # menos y nadie iría a buscar por qué.
            for repository in plan.repositories:
                if repository.classification == "UNDETERMINED":
                    print(
                        f"UNDETERMINED={repository.repo_id}|{repository.reason}|"
                        f"{repository.detail}"
                    )
            for repository in plan.repositories:
                if repository.classification in APPLICABLE:
                    branch = release_branch(
                        prefix=plan.branch_prefix,
                        skill_id=plan.skill_id,
                        skill_version=plan.skill_version,
                        plan_hash=plan.plan_hash,
                    )
                    print(f"BRANCH={repository.repo_id}|{branch}")
            print("WRITE_GATE=BLOCK")
            return 0
        plan = SyncPlan.load(Path(arguments.plan))
        result = apply_sync_plan(
            plan,
            confirmed_plan_hash=arguments.confirm_plan_hash,
            selected_repositories=tuple(arguments.repo),
            confirmed_by=arguments.confirmed_by,
            push_confirmed_by=arguments.push_confirmed_by,
            git_author_name=arguments.git_author_name,
            git_author_email=arguments.git_author_email,
            accept_risks_by=arguments.accept_risks_by,
            accept_adaptation_by=arguments.accept_adaptation_by,
        )
        print(f"SYNC={result.result}")
        for receipt in result.receipts:
            values = load_env(receipt)
            print(
                "REPOSITORY="
                f"{values['REPO_ID']}|{values['RESULT']}|{values['PUSH']}|{receipt}"
            )
        return 0 if result.result == "COMPLETE" else 1
    except (OSError, ValueError) as error:
        print(f"SYNC_ERROR={error}", file=sys.stderr)
        return 1

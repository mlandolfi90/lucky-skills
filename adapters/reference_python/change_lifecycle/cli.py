from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lifecycle_core.envfile import load_env

from .records import append_record, close_change, create_observation, record_autopsy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Registro de cambio Skills v3")
    commands = parser.add_subparsers(dest="command", required=True)

    observe = commands.add_parser("observe")
    _common_writer(observe)
    observe.add_argument("--summary", required=True)
    observe.add_argument("--scope", choices=("GLOBAL", "LOCAL"), required=True)
    observe.add_argument("--observed", default="")
    observe.add_argument("--expected", default="")

    record = commands.add_parser("record")
    _common_writer(record)
    record.add_argument("--change-id", required=True)
    record.add_argument(
        "--kind",
        required=True,
        choices=(
            "DIAGNOSIS",
            "MICROFIX",
            "HOTFIX",
            "FEATURE",
            "QUALITY",
            "REFACTOR",
            "MIGRATION",
        ),
    )
    record.add_argument("--summary", required=True)
    record.add_argument("--target-where", default="UNCONFIRMED")
    record.add_argument("--evidence", default="")
    record.add_argument("--rollback", default="")

    close = commands.add_parser("close")
    _common_writer(close)
    close.add_argument("--change-id", required=True)
    close.add_argument(
        "--status",
        required=True,
        choices=("FINAL", "CONDITIONAL", "BLOCKED"),
    )
    close.add_argument("--result", required=True)
    close.add_argument("--tests", required=True)
    close.add_argument("--architecture", required=True)
    close.add_argument("--collision", required=True)
    close.add_argument("--conditions", default="")

    autopsy = commands.add_parser("autopsy")
    _common_writer(autopsy)
    autopsy.add_argument("--change-id", required=True)
    autopsy.add_argument("--root-cause", required=True)
    autopsy.add_argument("--correction", required=True)
    autopsy.add_argument("--recovery-evidence", required=True)
    autopsy.add_argument("--prevention", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    workspace = Path(arguments.workspace)
    try:
        if arguments.command == "observe":
            path = create_observation(
                workspace=workspace,
                summary=arguments.summary,
                scope=arguments.scope,
                author=arguments.author,
                confirmed_by=arguments.confirmed_by,
                observed=arguments.observed,
                expected=arguments.expected,
            )
        elif arguments.command == "record":
            path = append_record(
                workspace=workspace,
                change_id=arguments.change_id,
                kind=arguments.kind,
                author=arguments.author,
                confirmed_by=arguments.confirmed_by,
                summary=arguments.summary,
                target_where=arguments.target_where,
                evidence=arguments.evidence,
                rollback=arguments.rollback,
            )
        elif arguments.command == "close":
            path = close_change(
                workspace=workspace,
                change_id=arguments.change_id,
                status=arguments.status,
                result=arguments.result,
                author=arguments.author,
                confirmed_by=arguments.confirmed_by,
                tests=arguments.tests,
                architecture=arguments.architecture,
                collision=arguments.collision,
                conditions=arguments.conditions,
            )
        else:
            path = record_autopsy(
                workspace=workspace,
                change_id=arguments.change_id,
                author=arguments.author,
                confirmed_by=arguments.confirmed_by,
                root_cause=arguments.root_cause,
                correction=arguments.correction,
                recovery_evidence=arguments.recovery_evidence,
                prevention=arguments.prevention,
            )
        values = load_env(path)
        print(f"CHANGE_ID={values['CHANGE_ID']}")
        print(f"KIND={values['KIND']}")
        print(f"SEQUENCE={values['SEQUENCE']}")
        print(f"AUTHOR={values['AUTHOR']}")
        print(f"RECEIPT={path.resolve()}")
        return 0
    except (OSError, ValueError) as error:
        print(f"CHANGE_ERROR={error}", file=sys.stderr)
        return 1


def _common_writer(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--confirmed-by", required=True)

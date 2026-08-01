from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lifecycle_core.suite_validator import validate_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validar el contrato portable de una suite de skills"
    )
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parents[2] / "skills"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        report = validate_suite(Path(arguments.skills_root))
    except (OSError, ValueError) as error:
        print("SUITE_VALIDATION=FAIL")
        print("SKILLS=0")
        print(f"ERROR={error}", file=sys.stderr)
        return 1

    print(f"SUITE_VALIDATION={'PASS' if report.ok else 'FAIL'}")
    print(f"SKILLS={len(report.manifests)}")
    for issue in report.issues:
        print(
            f"ERROR={issue.code}|{issue.path}|{issue.detail}",
            file=sys.stderr,
        )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

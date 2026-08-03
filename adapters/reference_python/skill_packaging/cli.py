from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from lifecycle_core.harness_catalog import harness_ids

from .packager import package_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Empaqueta skills para un harness soportado."
    )
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--catalog-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--skill", action="append", required=True, dest="skills")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        result = package_skills(
            repository_root=arguments.repository_root,
            catalog_root=arguments.catalog_root,
            output_root=arguments.output_root,
            skill_ids=tuple(arguments.skills),
            harness_id=arguments.harness,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR={error}")
        return 2
    print(f"HARNESS={result.harness_id}")
    print(f"SKILLS={','.join(result.skills)}")
    print(f"ARTIFACTS={len(result.artifacts)}")
    print(f"CONTENT_HASH={result.content_hash}")
    return 0

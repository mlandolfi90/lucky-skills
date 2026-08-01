from __future__ import annotations

import argparse


SOURCE_RESULTS = {"ALIGNED", "DRIFT", "PARTIAL", "STALE", "NOT_APPLICABLE"}
EVIDENCE_LEVELS = {"VERIFIED_DIRECT", "HUMAN_PROVIDED", "DECLARED", "UNKNOWN"}
README_POLICIES = {"IGNORE", "DISCOVERY_ONLY", "DECLARED_TRUST"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Triangula estado local, remoto, runtime y capacidades sin mutar."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument(
        "--source-root",
        default="",
        help="raíz que contiene VERSION; elimina supuestos sobre ancestros",
    )
    parser.add_argument(
        "--skill-version",
        default="",
        help="versión explícita para una copia autónoma del adaptador",
    )
    parser.add_argument("--harness", default="unknown")
    parser.add_argument(
        "--execution-level",
        choices=("NATIVE", "ADAPTED", "DEGRADED", "MANUAL"),
        default="ADAPTED",
    )
    parser.add_argument("--remote", default="")
    parser.add_argument("--remote-confirmed-by", default="")
    parser.add_argument("--remote-confirmed-source-id", default="")
    parser.add_argument(
        "--runtime-result",
        choices=("AUTO", *sorted(SOURCE_RESULTS - {"STALE"})),
        default="AUTO",
    )
    parser.add_argument("--runtime-version", default="UNKNOWN")
    parser.add_argument("--runtime-target", default="")
    parser.add_argument("--runtime-source", default="")
    parser.add_argument(
        "--runtime-evidence",
        choices=sorted(EVIDENCE_LEVELS),
        default="UNKNOWN",
    )
    parser.add_argument("--runtime-observed-at", default="")
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        metavar="KIND|NAME|STATE[|VERSION]",
    )
    parser.add_argument(
        "--capabilities-evidence",
        choices=sorted(EVIDENCE_LEVELS),
        default="VERIFIED_DIRECT",
    )
    parser.add_argument("--capabilities-observed-at", default="")
    parser.add_argument(
        "--readme-policy",
        choices=sorted(README_POLICIES),
        default=None,
    )
    parser.add_argument("--readme-policy-confirmed-by", default="")
    parser.add_argument(
        "--intent",
        choices=("read", "edit", "push", "deploy"),
        default="read",
    )
    parser.add_argument("--target-where", default="")
    parser.add_argument(
        "--target-action",
        choices=("EDIT", "PUSH", "DEPLOY"),
        default="",
    )
    parser.add_argument("--target-confirmed-by", default="")
    parser.add_argument("--timeout", type=int, default=0)
    parser.add_argument("--max-entries", type=int, default=0)
    parser.add_argument("--receipt-root", default="")
    parser.add_argument("--collected-by", default="session:mother")
    parser.add_argument("--synthesized-by", default="session:mother")
    parser.add_argument("--decided-by", default="NONE")
    return parser

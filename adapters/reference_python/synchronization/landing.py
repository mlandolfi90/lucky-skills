from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def create_landing_receipt(
    *,
    workspace: Path,
    harness: str,
    confirmed_by: str,
    receipt_root: Path,
) -> Path:
    adapter_root = Path(__file__).resolve().parents[1]
    source_root = Path(__file__).resolve().parents[3]
    before = set(receipt_root.rglob("sextante-*.env"))
    command = [
        sys.executable,
        "-B",
        str(adapter_root / "run_sextante.py"),
        "--workspace",
        str(workspace),
        "--source-root",
        str(source_root),
        "--harness",
        harness,
        "--execution-level",
        "NATIVE",
        "--runtime-result",
        "NOT_APPLICABLE",
        "--runtime-source",
        "sync:no-runtime",
        "--runtime-evidence",
        "VERIFIED_DIRECT",
        "--capability",
        f"harness|{harness}|INVOKABLE",
        "--capabilities-evidence",
        "VERIFIED_DIRECT",
        "--readme-policy",
        "IGNORE",
        "--intent",
        "edit",
        "--target-where",
        "local:workspace",
        "--target-action",
        "EDIT",
        "--target-confirmed-by",
        confirmed_by,
        "--receipt-root",
        str(receipt_root),
        "--collected-by",
        "session:mother:sincronizar",
        "--synthesized-by",
        "session:mother:sincronizar",
        "--decided-by",
        confirmed_by,
    ]
    completed = subprocess.run(
        command,
        cwd=source_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    if completed.returncode != 0 or "WRITE_GATE=PASS" not in completed.stdout:
        detail = " ".join((completed.stdout + " " + completed.stderr).split())
        raise ValueError(
            "Sextante no habilitó el TARGET remoto clonado: " + detail[:500]
        )
    created = set(receipt_root.rglob("sextante-*.env")) - before
    if len(created) != 1:
        raise ValueError("Sextante no produjo un comprobante inequívoco")
    return created.pop()

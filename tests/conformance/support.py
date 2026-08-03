from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_ROOT = ROOT / "adapters" / "reference_python"
SCRIPT = ADAPTER_ROOT / "run_sextante.py"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
VISIBLE_KEYS = (
    "LOCAL",
    "REMOTE",
    "RUNTIME",
    "CAPABILITIES",
    "STATE_VERDICT",
    "READ_GATE",
    "WRITE_GATE",
    "TARGET",
    "RECEIPT",
)
DECISION_KEYS = ("HUMAN_DECISION", "DECISION_REASON")
sys.path.insert(0, str(ADAPTER_ROOT))

from sextante.envfile import load_env  # noqa: E402
from sextante.receipt import verify_receipt  # noqa: E402


class AdapterHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()
        self.receipt_root = self.base / "receipts"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_adapter(
        self, *extra_arguments: str
    ) -> tuple[dict[str, str], dict[str, str]]:
        normalized_arguments = list(extra_arguments)
        if (
            _argument_value(normalized_arguments, "--runtime-result")
            == "NOT_APPLICABLE"
        ):
            if "--runtime-source" not in normalized_arguments:
                normalized_arguments.extend(["--runtime-source", "fixture:no-runtime"])
            if "--runtime-evidence" not in normalized_arguments:
                normalized_arguments.extend(["--runtime-evidence", "VERIFIED_DIRECT"])
        completed = run_adapter_process(
            script=SCRIPT,
            workspace=self.workspace,
            receipt_root=self.receipt_root,
            extra_arguments=normalized_arguments,
            cwd=ROOT,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        summary = parse_visible_summary(completed.stdout)
        receipt_path = self.last_receipt_path()
        self.assertTrue(receipt_path.is_file())
        self.assertTrue(verify_receipt(receipt_path))
        return summary, load_env(receipt_path)

    def last_receipt_path(self, root: Path | None = None) -> Path:
        receipt_root = root or self.receipt_root
        receipts = sorted(receipt_root.rglob("sextante-*.env"))
        self.assertTrue(receipts)
        return receipts[-1]

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["git", "-C", str(self.workspace), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed

    def init_committed_repository(self) -> None:
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Sextante Test")
        self.git("config", "user.email", "sextante@example.invalid")
        (self.workspace / "module.py").write_text("value = 1\n", encoding="utf-8")
        self.git("add", "module.py")
        self.git("commit", "-m", "test: initial state")


def run_adapter_process(
    *,
    script: Path,
    workspace: Path,
    receipt_root: Path,
    extra_arguments: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(script),
            "--workspace",
            str(workspace),
            "--harness",
            "codex",
            "--receipt-root",
            str(receipt_root),
            *extra_arguments,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def parse_visible_summary(stdout: str) -> dict[str, str]:
    lines = stdout.splitlines()
    expected_keys = VISIBLE_KEYS
    if len(lines) == len(VISIBLE_KEYS) + len(DECISION_KEYS):
        expected_keys += DECISION_KEYS
    if len(lines) != len(expected_keys):
        raise AssertionError(f"cantidad de líneas visible inválida: {lines!r}")

    values: dict[str, str] = {}
    actual_keys: list[str] = []
    for line in lines:
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise AssertionError(f"línea visible inválida o duplicada: {line!r}")
        actual_keys.append(key)
        values[key] = value
    if tuple(actual_keys) != expected_keys:
        raise AssertionError(f"orden/clave visible inválido: {tuple(actual_keys)!r}")
    return values


def state_map_fixture(*, local_commit: str) -> str:
    return (
        'STATE_SCHEMA="1"\n'
        'STATE_REVISION="0"\n'
        f'GIT_LOCAL_COMMIT="{local_commit}"\n'
        'GIT_LOCAL_FINGERPRINT="UNKNOWN"\n'
        'GIT_REMOTE_COMMIT="UNKNOWN"\n'
        'GIT_REMOTE_REF="UNKNOWN"\n'
        'RUNTIME_VERSION="UNKNOWN"\n'
        'CAPABILITIES_HASH="UNKNOWN"\n'
        'TARGET_WHERE="UNCONFIRMED"\n'
        'TARGET_ACTION="UNCONFIRMED"\n'
        'TARGET_CONFIRMED_BY="UNCONFIRMED"\n'
    )


def write_utf8_lf(path: Path, content: str) -> None:
    path.write_bytes(content.encode("utf-8"))


def _argument_value(arguments: list[str], name: str) -> str:
    try:
        return arguments[arguments.index(name) + 1]
    except (ValueError, IndexError):
        return ""


def seed_adapters(repository_root: Path) -> None:
    """Sembrar los contratos de harness que el catálogo declara.

    Un catálogo declara sus harnesses en `adapters/<harness>/PACKAGING.env`:
    es de ahí que salen el prefijo de proyección y las exclusiones. Un
    catálogo de prueba sin ellos no modelaba un catálogo real.
    """
    destino = repository_root / "adapters"
    destino.mkdir(parents=True, exist_ok=True)
    for contrato in sorted((ROOT / "adapters").glob("*/PACKAGING.env")):
        carpeta = destino / contrato.parent.name
        carpeta.mkdir(exist_ok=True)
        shutil.copy2(contrato, carpeta / "PACKAGING.env")

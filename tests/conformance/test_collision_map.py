from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT, ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from collision_map.scanner import scan_collisions  # noqa: E402
from lifecycle_core.envfile import load_env  # noqa: E402


class CollisionMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_clean_unversioned_workspace_has_no_collision(self) -> None:
        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/domain/order.py",),
        )
        self.assertEqual(report.state, "NONE")
        self.assertEqual(report.recommendation, "CONTINUE")

    def test_claim_detects_path_symbol_contract_and_base_mismatch(self) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True)
        (claims / "other.env").write_text(
            (
                'STATUS="ACTIVE"\n'
                'ACTOR="session:other"\n'
                'PATHS="src/domain"\n'
                'SYMBOLS="Order"\n'
                'CONTRACTS="OrderPort"\n'
                'BASE_FINGERPRINT="old"\n'
            ),
            encoding="utf-8",
        )
        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/domain/order.py",),
            symbols=("Order",),
            contracts=("OrderPort",),
            base_fingerprint="new",
        )
        self.assertEqual(report.state, "FOUND")
        self.assertEqual(report.base_mismatch, "YES")
        self.assertEqual(
            {collision.kind for collision in report.collisions},
            {"PATH", "SYMBOL", "CONTRACT", "BASE_MISMATCH"},
        )

    def test_inactive_claim_is_ignored(self) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True)
        (claims / "done.env").write_text(
            'STATUS="CLOSED"\nACTOR="session:other"\nPATHS="src"\n',
            encoding="utf-8",
        )
        report = scan_collisions(workspace=self.workspace, paths=("src/a.py",))
        self.assertEqual(report.state, "NONE")

    def test_relevant_claims_with_distinct_bases_block_without_explicit_base(
        self,
    ) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True)
        for name, actor, base in (
            ("alpha", "agent:alpha", "base-alpha"),
            ("beta", "agent:beta", "base-beta"),
        ):
            (claims / f"{name}.env").write_text(
                (
                    'STATUS="ACTIVE"\n'
                    f'ACTOR="{actor}"\n'
                    'PATHS="src/orders"\n'
                    f'BASE_FINGERPRINT="{base}"\n'
                ),
                encoding="utf-8",
            )

        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/orders/service.py",),
        )

        self.assertEqual(report.state, "FOUND")
        self.assertEqual(report.base_mismatch, "YES")
        self.assertEqual(report.recommendation, "BLOCK")
        self.assertEqual(
            {
                (item.kind, item.subject, item.actor)
                for item in report.collisions
                if item.kind == "BASE_MISMATCH"
            },
            {
                ("BASE_MISMATCH", "base-alpha", "agent:alpha"),
                ("BASE_MISMATCH", "base-beta", "agent:beta"),
            },
        )

    def test_incompatible_criterion_replans_but_equal_criterion_does_not(self) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True)
        (claims / "other.env").write_text(
            (
                'STATUS="ACTIVE"\n'
                'ACTOR="session:other"\n'
                'CRITERIA="order-storage=repository"\n'
                'BASE_FINGERPRINT="same-base"\n'
            ),
            encoding="utf-8",
        )

        equal = scan_collisions(
            workspace=self.workspace,
            paths=(),
            criteria=("order-storage=repository",),
        )
        conflict = scan_collisions(
            workspace=self.workspace,
            paths=(),
            criteria=("order-storage=service",),
        )

        self.assertEqual(equal.state, "NONE")
        self.assertEqual(equal.recommendation, "CONTINUE")
        self.assertEqual(conflict.state, "FOUND")
        self.assertEqual(conflict.recommendation, "REPLAN")
        self.assertEqual(
            conflict.criteria,
            ("order-storage=repository->service",),
        )

    def test_cli_receipt_preserves_actor_subject_associations(self) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True)
        (claims / "other.env").write_text(
            (
                'STATUS="ACTIVE"\n'
                'ACTOR="agent:other"\n'
                'PATHS="src/orders"\n'
                'BASE_FINGERPRINT="base-a"\n'
            ),
            encoding="utf-8",
        )
        receipts = self.workspace / "receipts"
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ADAPTER_ROOT / "run_collision_map.py"),
                "--workspace",
                str(self.workspace),
                "--path",
                "src/orders/service.py",
                "--receipt-root",
                str(receipts),
                "--collected-by",
                "agent:test",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        receipt_paths = tuple(receipts.glob("collision-*.env"))
        self.assertEqual(len(receipt_paths), 1)
        values = load_env(receipt_paths[0])
        self.assertEqual(values["COLLECTED_BY"], "agent:test")
        evidence = json.loads(values["EVIDENCE"])
        self.assertIn(
            {
                "actor": "agent:other",
                "kind": "PATH",
                "source": ".lifecycle/local/claims/other.env",
                "subject": "src/orders",
            },
            evidence,
        )


class ReceiptQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run_cli(self, receipts: Path) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ADAPTER_ROOT / "run_collision_map.py"),
                "--workspace",
                str(self.workspace),
                "--path",
                "src/api.py",
                "--symbol",
                "handler",
                "--receipt-root",
                str(receipts),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_receipt_records_query_with_reproducible_hash(self) -> None:
        # Sin el alcance consultado, un COLLISION=NONE no distingue "consulté
        # y no había nada" de "no consulté nada". QUERY_HASH es la clave de
        # deduplicación independiente del reloj.
        first_root = self.workspace / "r1"
        second_root = self.workspace / "r2"
        self._run_cli(first_root)
        self._run_cli(second_root)
        first = load_env(next(iter(first_root.glob("collision-*.env"))))
        second = load_env(next(iter(second_root.glob("collision-*.env"))))

        self.assertEqual(first["QUERY_PATHS"], "src/api.py")
        self.assertEqual(first["QUERY_SYMBOLS"], "handler")
        self.assertEqual(first["QUERY_CONTRACTS"], "NONE")
        self.assertEqual(first["QUERY_BASE_FINGERPRINT"], "NONE")
        self.assertEqual(first["QUERY_HASH"], second["QUERY_HASH"])


class GitQuotingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.workspace), *arguments],
            capture_output=True,
            check=True,
        )

    def test_special_paths_come_back_decoded(self) -> None:
        # git C-quotea los paths con espacios o no-ASCII; propagar la forma
        # cruda (`"docs/con espacio \303\261.md"`) rompe cualquier comparación
        # contra el nombre real del archivo.
        self._git("init")
        self._git("config", "user.email", "conformance@example.test")
        self._git("config", "user.name", "conformance")
        docs = self.workspace / "docs"
        docs.mkdir()
        special = docs / "con espacio ñ, coma.md"
        special.write_text("contenido\n", encoding="utf-8")

        report = scan_collisions(workspace=self.workspace, paths=("docs",))

        self.assertEqual(report.state, "FOUND")
        self.assertIn("docs/con espacio ñ, coma.md", report.paths)


class BaseMismatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_claim(self, base: str) -> None:
        claims = self.workspace / ".lifecycle" / "local" / "claims"
        claims.mkdir(parents=True, exist_ok=True)
        (claims / "otra.env").write_text(
            (
                'STATUS="ACTIVE"\n'
                'ACTOR="session:otra"\n'
                'PATHS="src/api.py"\n'
                f'BASE_FINGERPRINT="{base}"\n'
            ),
            encoding="utf-8",
        )

    def test_without_comparable_base_reports_unknown_not_no(self) -> None:
        # `NO` afirma que la comparación ocurrió; sin claims no ocurrió nada.
        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/api.py",),
            base_fingerprint="a" * 64,
        )
        self.assertEqual(report.base_mismatch, "UNKNOWN")
        # Informativo: no debe volcar el veredicto global a BLOCK.
        self.assertEqual(report.state, "NONE")
        self.assertEqual(report.recommendation, "CONTINUE")

    def test_matching_bases_report_no(self) -> None:
        self._write_claim("a" * 64)
        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/api.py",),
            base_fingerprint="a" * 64,
        )
        self.assertEqual(report.base_mismatch, "NO")

    def test_divergent_bases_block_and_name_the_conflict(self) -> None:
        self._write_claim("1" * 64)
        report = scan_collisions(
            workspace=self.workspace,
            paths=("src/api.py",),
            base_fingerprint="2" * 64,
        )
        self.assertEqual(report.base_mismatch, "YES")
        self.assertEqual(report.recommendation, "BLOCK")
        conflict = next(
            item for item in report.collisions if item.kind == "BASE_MISMATCH"
        )
        self.assertEqual(conflict.actor, "session:otra")
        self.assertEqual(conflict.source, ".lifecycle/local/claims/otra.env")

    def test_cli_emits_warning_conflict_and_proposal(self) -> None:
        self._write_claim("1" * 64)
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ADAPTER_ROOT / "run_collision_map.py"),
                "--workspace",
                str(self.workspace),
                "--path",
                "src/api.py",
                "--base-fingerprint",
                "2" * 64,
                "--receipt-root",
                str(self.workspace / "receipts"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("WARNING=", completed.stdout)
        self.assertIn("CONFLICT=session:otra|base:111111111111|", completed.stdout)
        self.assertIn("PROPOSAL=replanificar sobre la base actual", completed.stdout)


class UnreadableWorktreeTests(unittest.TestCase):
    """Un repositorio ilegible no puede parecerse a uno sin colisiones.

    Si la única fuente de evidencia falla y el veredicto es `NONE`/`CONTINUE`,
    la compuerta autoriza escribir justo cuando dejó de poder mirar.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.workspace), *arguments],
            capture_output=True,
            check=True,
        )

    def _seed_dirty_repository(self) -> None:
        self._git("init")
        self._git("config", "user.email", "conformance@example.test")
        self._git("config", "user.name", "conformance")
        (self.workspace / "shared.py").write_text("base\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-m", "base")
        (self.workspace / "shared.py").write_text("base\ncambio\n", encoding="utf-8")

    def test_dirty_repository_is_detected(self) -> None:
        self._seed_dirty_repository()
        report = scan_collisions(workspace=self.workspace, paths=("shared.py",))
        self.assertEqual(report.state, "FOUND")
        self.assertEqual(report.recommendation, "COORDINATE")

    def test_unreadable_repository_blocks_instead_of_reporting_none(self) -> None:
        self._seed_dirty_repository()
        (self.workspace / ".git" / "HEAD").write_text("basura\n", encoding="utf-8")
        report = scan_collisions(workspace=self.workspace, paths=("shared.py",))
        self.assertEqual(report.state, "UNKNOWN")
        self.assertEqual(report.recommendation, "BLOCK")
        self.assertEqual(report.base_mismatch, "UNKNOWN")

    def test_directory_without_git_stays_usable(self) -> None:
        (self.workspace / "a.py").write_text("hola\n", encoding="utf-8")
        report = scan_collisions(workspace=self.workspace, paths=("a.py",))
        self.assertEqual(report.state, "NONE")
        self.assertEqual(report.recommendation, "CONTINUE")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT, seed_adapters

sys.path.insert(0, str(ADAPTER_ROOT))

from lifecycle_core.envfile import canonical_env, load_env  # noqa: E402
from sextante.local_probe import probe_local  # noqa: E402
from synchronization.branches import release_branch  # noqa: E402
from synchronization.landing import create_landing_receipt  # noqa: E402
from synchronization.models import RepositoryAssessment, SyncPlan  # noqa: E402
from synchronization.registry import load_registry  # noqa: E402
from synchronization.transaction import apply_sync_plan  # noqa: E402
from synchronization.scanner import build_sync_plan  # noqa: E402
from synchronization.transaction import apply_sync_plan  # noqa: E402


class SynchronizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.catalog = self.base / "catalog" / "skills"
        self.registry = self.base / "registry" / "repos"
        self.catalog.mkdir(parents=True)
        seed_adapters(self.catalog.parent)
        self.registry.mkdir(parents=True)
        self._write_skill()
        self.remote = self._remote()
        self._write_registry(self.remote)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_remote_adoption_pushes_isolated_branch_and_becomes_current(self) -> None:
        plan = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
        )
        assessment = plan.repositories[0]
        self.assertEqual(assessment.classification, "NEEDS_ADAPTATION")
        self.assertTrue(assessment.transition_hash != "NONE")
        self.assertEqual(plan.branch_prefix, "codex/")

        applied = apply_sync_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            selected_repositories=("example",),
            confirmed_by="human:test",
            push_confirmed_by="human:test",
            git_author_name="Test Human",
            git_author_email="test@example.invalid",
        )
        self.assertEqual(applied.result, "COMPLETE", load_env(applied.receipts[0]))
        receipt = load_env(applied.receipts[0])
        self.assertEqual(receipt["RESULT"], "COMPLETE")
        self.assertEqual(receipt["PUSH"], "PUSHED")
        branch = receipt["BRANCH"]
        self.assertTrue(self._git_bare("rev-parse", f"refs/heads/{branch}"))

        inspection = self.base / "inspection"
        self._run(
            "git",
            "clone",
            "--branch",
            branch,
            "--",
            str(self.remote),
            str(inspection),
        )
        self.assertTrue((inspection / "skills" / "demo" / "SKILL.md").is_file())
        self.assertTrue(
            (inspection / ".agents" / "skills" / "demo" / "SKILL.md").is_file()
        )
        observed, _ = probe_local(
            inspection,
            timeout_seconds=10,
            max_entries=50_000,
        )
        state_map = load_env(inspection / ".lifecycle" / "state" / "STATE-MAP.env")
        self.assertEqual(
            observed.fingerprint,
            state_map["GIT_LOCAL_FINGERPRINT"],
            {
                "observed": observed,
                "state_map": state_map,
            },
        )
        create_landing_receipt(
            workspace=inspection,
            harness="codex",
            confirmed_by="human:test",
            receipt_root=self.base / "landing-check",
        )

        self._write_registry(self.remote, default_branch=branch)
        current = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
        )
        self.assertEqual(current.repositories[0].classification, "CURRENT")

    def test_existing_divergent_branch_is_not_force_pushed(self) -> None:
        plan = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
        )
        branch = f"codex/skills-demo-v1.0.0-{plan.plan_hash[:8]}"
        intruder = self.base / "intruder"
        self._run("git", "clone", "--", str(self.remote), str(intruder))
        self._run("git", "-C", str(intruder), "config", "user.name", "Other")
        self._run(
            "git",
            "-C",
            str(intruder),
            "config",
            "user.email",
            "other@example.invalid",
        )
        self._run("git", "-C", str(intruder), "checkout", "-b", branch)
        (intruder / "other.txt").write_text("divergent\n", encoding="utf-8")
        self._run("git", "-C", str(intruder), "add", "other.txt")
        self._run("git", "-C", str(intruder), "commit", "-m", "diverge")
        self._run(
            "git",
            "-C",
            str(intruder),
            "push",
            "origin",
            f"HEAD:refs/heads/{branch}",
        )
        before = self._git_bare("rev-parse", f"refs/heads/{branch}")

        applied = apply_sync_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            selected_repositories=("example",),
            confirmed_by="human:test",
            push_confirmed_by="human:test",
            git_author_name="Test Human",
            git_author_email="test@example.invalid",
        )
        receipt = load_env(applied.receipts[0])
        self.assertEqual(receipt["RESULT"], "HUMAN_REQUIRED", receipt)
        self.assertEqual(receipt["PUSH"], "REJECTED")
        self.assertEqual(
            self._git_bare("rev-parse", f"refs/heads/{branch}"),
            before,
        )

    def test_batch_continues_safe_repositories_after_one_push_rejection(
        self,
    ) -> None:
        second_remote = self._remote("-second")
        self._write_registry(second_remote, repo_id="second")
        plan = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
        )
        branch = release_branch(
            prefix=plan.branch_prefix,
            skill_id=plan.skill_id,
            skill_version=plan.skill_version,
            plan_hash=plan.plan_hash,
        )
        self._create_divergent_branch(second_remote, branch)

        applied = apply_sync_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            selected_repositories=("example", "second"),
            confirmed_by="human:batch",
            push_confirmed_by="human:push",
            git_author_name="Test Human",
            git_author_email="test@example.invalid",
        )

        self.assertEqual(applied.result, "PARTIAL")
        by_repo = {
            load_env(path)["REPO_ID"]: load_env(path) for path in applied.receipts
        }
        self.assertEqual(by_repo["example"]["RESULT"], "COMPLETE")
        self.assertEqual(by_repo["second"]["RESULT"], "HUMAN_REQUIRED")
        self.assertEqual(by_repo["second"]["REASON"], "PUSH_REJECTED")
        self.assertEqual(by_repo["example"]["CONFIRMED_BY"], "human:batch")
        self.assertEqual(by_repo["example"]["PUSH_CONFIRMED_BY"], "human:push")
        self.assertEqual(by_repo["example"]["GIT_AUTHOR_NAME"], "Test Human")
        self.assertTrue(self._git_bare("rev-parse", f"refs/heads/{branch}"))

    def test_branch_prefix_is_bound_into_the_confirmed_plan(self) -> None:
        default = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
        )
        alternate = build_sync_plan(
            catalog=self.catalog,
            registry=self.registry,
            skill_id="demo",
            confirmed_by="human:test",
            branch_prefix="automation/",
        )

        self.assertNotEqual(default.plan_hash, alternate.plan_hash)
        self.assertEqual(alternate.branch_prefix, "automation/")

    def test_registry_rejects_embedded_credentials(self) -> None:
        self._write_registry(
            "https://user:secret@example.invalid/repo.git",
        )
        with self.assertRaisesRegex(ValueError, "credenciales"):
            load_registry(self.registry)

    def test_registry_rejects_git_remote_helpers(self) -> None:
        self._write_registry("ext::sh -c touch% /tmp/pwned")
        with self.assertRaisesRegex(ValueError, "helper Git"):
            load_registry(self.registry)

    def _write_skill(self) -> None:
        skill = self.catalog / "demo"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: demo\n"
            "description: Skill portable para el canario remoto.\n"
            "---\n\n"
            "# Demo\n",
            encoding="utf-8",
            newline="\n",
        )
        (skill / "manifest.env").write_text(
            'FORMAT_VERSION="1"\n'
            'SKILL_ID="demo"\n'
            'SKILL_VERSION="1.0.0"\n'
            'REQUIRES=""\n',
            encoding="utf-8",
            newline="\n",
        )
        (skill / ".gitattributes").write_text(
            "* text=auto eol=lf\n",
            encoding="utf-8",
            newline="\n",
        )

    def _remote(self, suffix: str = "") -> Path:
        source = self.base / f"source{suffix}"
        source.mkdir()
        self._run("git", "init", "-b", "main", str(source))
        self._run("git", "-C", str(source), "config", "user.name", "Fixture")
        self._run(
            "git",
            "-C",
            str(source),
            "config",
            "user.email",
            "fixture@example.invalid",
        )
        (source / "README.md").write_text("fixture\n", encoding="utf-8")
        self._run("git", "-C", str(source), "add", "README.md")
        self._run("git", "-C", str(source), "commit", "-m", "initial")
        remote = self.base / f"remote{suffix}.git"
        self._run("git", "clone", "--bare", "--", str(source), str(remote))
        return remote

    def _write_registry(
        self,
        remote: Path | str,
        *,
        default_branch: str = "main",
        repo_id: str = "example",
    ) -> None:
        values = {
            "FORMAT_VERSION": "1",
            "REPO_ID": repo_id,
            "REMOTE_URL": str(remote),
            "DEFAULT_BRANCH": default_branch,
            "HARNESS": "codex",
            "SKILLS": "demo",
            "STATUS": "ACTIVE",
        }
        (self.registry / f"{repo_id}.env").write_text(
            canonical_env(values),
            encoding="utf-8",
            newline="\n",
        )

    def _create_divergent_branch(self, remote: Path, branch: str) -> None:
        intruder = self.base / f"intruder-{remote.stem}"
        self._run("git", "clone", "--", str(remote), str(intruder))
        self._run("git", "-C", str(intruder), "config", "user.name", "Other")
        self._run(
            "git",
            "-C",
            str(intruder),
            "config",
            "user.email",
            "other@example.invalid",
        )
        self._run("git", "-C", str(intruder), "checkout", "-b", branch)
        (intruder / "other.txt").write_text("divergent\n", encoding="utf-8")
        self._run("git", "-C", str(intruder), "add", "other.txt")
        self._run("git", "-C", str(intruder), "commit", "-m", "diverge")
        self._run(
            "git",
            "-C",
            str(intruder),
            "push",
            "origin",
            f"HEAD:refs/heads/{branch}",
        )

    def _git_bare(self, *arguments: str) -> str:
        return self._run(
            "git",
            "--git-dir",
            str(self.remote),
            *arguments,
        ).stdout.strip()

    def _run(self, *command: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"{' '.join(command)}\n{completed.stdout}\n{completed.stderr}",
        )
        return completed


class MajorJumpAcceptanceTests(unittest.TestCase):
    """El salto MAJOR no se entrega con la misma ceremonia que lo compatible.

    NEEDS_ADAPTATION mezcla adopción inicial (aplicar está bien) con salto
    MAJOR (entregar una ruptura a un repo no adaptado): el segundo exige
    aceptación humana explícita. Encontrado en vivo por el sandbox de
    migración MAJOR: el apply empujó la 2.0.0 a un repo clasificado
    NEEDS_ADAPTATION sin pedir nada.
    """

    def _plan(self, reason: str) -> SyncPlan:
        assessment = RepositoryAssessment(
            repo_id="r-uno",
            remote_url="C:/no/existe.git",
            default_branch="main",
            harness="codex",
            remote_head="a" * 40,
            observed_version="1.0.0",
            classification="NEEDS_ADAPTATION",
            reason=reason,
            transition_hash="b" * 16,
            changes=(),
            risks=(),
            collisions=(),
        )
        return SyncPlan(
            catalog="C:/no/existe/skills",
            registry="C:/no/existe/registry",
            skill_id="demo",
            skill_version="2.0.0",
            branch_prefix="codex/",
            source_hash="c" * 64,
            repositories=(assessment,),
        ).with_hash()

    def test_major_jump_requires_explicit_acceptance(self) -> None:
        plan = self._plan("MAJOR_OR_INITIAL_ADAPTATION")
        with self.assertRaisesRegex(ValueError, "accept_adaptation_by"):
            apply_sync_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                selected_repositories=("r-uno",),
                confirmed_by="human:test",
                push_confirmed_by="human:test",
                git_author_name="sync",
                git_author_email="sync@test",
            )

    def test_initial_adoption_passes_the_acceptance_gate(self) -> None:
        plan = self._plan("INITIAL_ADOPTION")
        # Debe atravesar la compuerta de aceptación; falla después por el
        # catálogo inexistente, lo que prueba que el gate no lo detuvo.
        with self.assertRaises((OSError, ValueError)) as raised:
            apply_sync_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                selected_repositories=("r-uno",),
                confirmed_by="human:test",
                push_confirmed_by="human:test",
                git_author_name="sync",
                git_author_email="sync@test",
            )
        self.assertNotIn("accept_adaptation_by", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

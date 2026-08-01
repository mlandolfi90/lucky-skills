from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT, ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from change_lifecycle.records import (  # noqa: E402
    append_record,
    close_change,
    create_observation,
)
from lifecycle_core.envfile import load_env  # noqa: E402
from lifecycle_core.receipts import verify_receipt  # noqa: E402
from publication.publisher import (  # noqa: E402
    _canary_hash,
    apply_release,
    build_release_plan,
)


class PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.extra_temporaries: list[tempfile.TemporaryDirectory[str]] = []
        self.workspace = Path(self.temporary.name)
        (self.workspace / ".lifecycle" / "local").mkdir(parents=True)
        self.catalog = self.workspace / "skills"
        for harness in ("claude-ai", "claude-code", "codex"):
            adapter = self.workspace / "adapters" / harness
            adapter.mkdir(parents=True)
            shutil.copy2(
                ROOT / "adapters" / harness / "PACKAGING.env",
                adapter / "PACKAGING.env",
            )
        self.skill = self.catalog / "demo"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\n"
            "name: demo\n"
            "description: Demostrar la publicación mínima.\n"
            "---\n\n"
            "# Demo\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.skill / "manifest.env").write_text(
            'FORMAT_VERSION="1"\n'
            'SKILL_ID="demo"\n'
            'SKILL_VERSION="1.2.3"\n'
            'REQUIRES=""\n',
            encoding="utf-8",
            newline="\n",
        )

    def tearDown(self) -> None:
        for temporary in self.extra_temporaries:
            temporary.cleanup()
        self.temporary.cleanup()

    def test_release_requires_exact_plan_and_updates_only_manifest(self) -> None:
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="PATCH",
            closure_receipt=self._closure(),
        )
        with self.assertRaisesRegex(ValueError, "PLAN_HASH"):
            apply_release(
                plan,
                confirmed_plan_hash="wrong",
                confirmed_by="human:test",
            )
        receipt = apply_release(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )
        self.assertEqual(
            load_env(self.skill / "manifest.env")["SKILL_VERSION"], "1.2.4"
        )
        values = load_env(receipt)
        self.assertEqual(values["RELEASE"], "READY")
        self.assertEqual(values["CANARY_HASH"], _canary_hash(self.catalog, "demo"))
        self.assertTrue(verify_receipt(receipt))

    def test_plan_becomes_stale_when_skill_changes(self) -> None:
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="MINOR",
            closure_receipt=self._closure(),
        )
        with (self.skill / "SKILL.md").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write("\nCambio paralelo.\n")
        with self.assertRaisesRegex(ValueError, "cambió"):
            apply_release(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
            )

    def test_authorized_git_release_commits_tags_and_pushes_atomically(self) -> None:
        remote = self._initialize_git_remote()
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="PATCH",
            closure_receipt=self._closure(),
        )

        receipt = apply_release(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:release",
            create_commit=True,
            commit_confirmed_by="human:commit",
            create_tag=True,
            tag_confirmed_by="human:tag",
            push=True,
            push_confirmed_by="human:push",
        )

        values = load_env(receipt)
        self.assertEqual(values["RELEASE"], "PUBLISHED")
        self.assertEqual(values["PUSH"], "PUSHED")
        changelog = (self.workspace / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## demo 1.2.4", changelog)
        self.assertIn("autorizó human:release", changelog)
        committed = self._run(
            "git", "-C", str(self.workspace),
            "show", "--name-only", "--format=", "HEAD",
        ).stdout
        self.assertIn("CHANGELOG.md", committed)
        self.assertEqual(values["COMMIT_CONFIRMED_BY"], "human:commit")
        self.assertEqual(values["TAG_CONFIRMED_BY"], "human:tag")
        self.assertEqual(values["PUSH_CONFIRMED_BY"], "human:push")
        self.assertEqual(
            self._run(
                "git",
                "--git-dir",
                str(remote),
                "rev-parse",
                "refs/heads/main",
            ).stdout.strip(),
            values["COMMIT"],
        )
        self.assertEqual(
            self._run(
                "git",
                "--git-dir",
                str(remote),
                "rev-parse",
                f"refs/tags/{values['TAG']}^{{commit}}",
            ).stdout.strip(),
            values["COMMIT"],
        )

    def test_tag_rejection_after_commit_is_recorded_for_human_resolution(
        self,
    ) -> None:
        self._initialize_git_remote()
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="PATCH",
            closure_receipt=self._closure(),
        )
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "tag",
            f"skill-demo-v{plan.to_version}",
        )

        receipt = apply_release(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:release",
            create_commit=True,
            commit_confirmed_by="human:commit",
            create_tag=True,
            tag_confirmed_by="human:tag",
        )

        values = load_env(receipt)
        self.assertNotEqual(values["COMMIT"], "NO")
        self.assertEqual(values["TAG"], "REJECTED")
        self.assertEqual(values["RELEASE"], "HUMAN_REQUIRED")
        self.assertEqual(values["REASON"], "TAG_REJECTED")
        self.assertEqual(
            load_env(self.skill / "manifest.env")["SKILL_VERSION"],
            plan.to_version,
        )

    def test_closure_is_consumed_by_a_single_release(self) -> None:
        closure = self._closure()
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="PATCH",
            closure_receipt=closure,
        )
        apply_release(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )

        # El mismo cierre no autoriza una segunda release.
        with self.assertRaisesRegex(ValueError, "consumido"):
            build_release_plan(
                catalog=self.catalog,
                skill_id="demo",
                impact="PATCH",
                closure_receipt=closure,
            )

    def test_release_without_content_change_is_rejected(self) -> None:
        self._initialize_git_remote()
        # Tag de la versión vigente sobre el contenido actual: no hay nada
        # nuevo que publicar.
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "tag",
            "skill-demo-v1.2.3",
        )
        with self.assertRaisesRegex(ValueError, "sin cambios de contenido"):
            build_release_plan(
                catalog=self.catalog,
                skill_id="demo",
                impact="PATCH",
                closure_receipt=self._closure(),
            )

        # Con un cambio real, la publicación vuelve a habilitarse.
        with (self.skill / "SKILL.md").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write("\nCambio real.\n")
        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="PATCH",
            closure_receipt=self._closure(),
        )
        self.assertEqual(plan.to_version, "1.2.4")

    def test_tag_is_annotated_and_auto_impact_proposed_from_commits(self) -> None:
        remote = self._initialize_git_remote()
        # Historia: release 1.2.3 taggeada, luego un feat sobre la skill.
        self._run("git", "-C", str(self.workspace), "tag", "-a",
                  "skill-demo-v1.2.3", "-m", "release demo 1.2.3")
        with (self.skill / "SKILL.md").open(
            "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write("\nNueva capacidad.\n")
        self._run("git", "-C", str(self.workspace), "add", "skills")
        self._run("git", "-C", str(self.workspace), "commit", "-m",
                  "feat(demo): nueva capacidad")

        plan = build_release_plan(
            catalog=self.catalog,
            skill_id="demo",
            impact="AUTO",
            closure_receipt=self._closure(),
        )
        # feat desde el último tag → MINOR propuesto, dentro del PLAN_HASH.
        self.assertEqual(plan.impact, "MINOR")
        self.assertEqual(plan.to_version, "1.3.0")

        apply_release(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:release",
            create_commit=True,
            commit_confirmed_by="human:commit",
            create_tag=True,
            tag_confirmed_by="human:tag",
        )
        # Tag anotado: el objeto del tag es "tag", no "commit".
        object_type = self._run(
            "git", "-C", str(self.workspace),
            "cat-file", "-t", "skill-demo-v1.3.0",
        ).stdout.strip()
        self.assertEqual(object_type, "tag")
        self.assertTrue(remote)

    def _closure(self) -> Path:
        observation = create_observation(
            workspace=self.workspace,
            summary="publish demo",
            scope="GLOBAL",
            author="human:test",
            confirmed_by="human:test",
            expected="released",
        )
        change_id = load_env(observation)["CHANGE_ID"]
        append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="DIAGNOSIS",
            author="session:mother:test",
            confirmed_by="human:test",
            summary="release ready",
        )
        return close_change(
            workspace=self.workspace,
            change_id=change_id,
            status="FINAL",
            result="quality passed",
            author="session:mother:test",
            confirmed_by="human:test",
            tests="PASS",
            architecture="PASS",
            collision="NONE",
        )

    def _initialize_git_remote(self) -> Path:
        self._run("git", "init", "-b", "main", str(self.workspace))
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "config",
            "user.name",
            "Test Human",
        )
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "config",
            "user.email",
            "test@example.invalid",
        )
        self._run("git", "-C", str(self.workspace), "add", "skills", "adapters")
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "commit",
            "-m",
            "initial catalog",
        )
        remote_temporary = tempfile.TemporaryDirectory()
        self.extra_temporaries.append(remote_temporary)
        remote = Path(remote_temporary.name) / "remote.git"
        self._run("git", "clone", "--bare", "--", str(self.workspace), str(remote))
        self._run(
            "git",
            "-C",
            str(self.workspace),
            "remote",
            "add",
            "origin",
            str(remote),
        )
        return remote

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


if __name__ == "__main__":
    unittest.main()

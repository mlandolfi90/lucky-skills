from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from support import ADAPTER_ROOT, ROOT


sys.path.insert(0, str(ADAPTER_ROOT))

from lifecycle_core.hashing import sha256_file  # noqa: E402
from skill_packaging.packager import PackagingResult, package_skills  # noqa: E402


class SkillPackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.output = self.base / "output"
        self.catalog = self.base / "skills"
        self.catalog.mkdir()
        self.write_skill("alpha")
        self.write_skill("beta", requires="alpha@1.0.0")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_claude_code_projects_dependency_closure_without_codex_metadata(
        self,
    ) -> None:
        result = self.package("claude-code", "beta")

        self.assertEqual(result.skills, ("alpha", "beta"))
        for skill_id in result.skills:
            skill_root = self.output / ".claude" / "skills" / skill_id
            self.assertTrue((skill_root / "SKILL.md").is_file())
            self.assertTrue((skill_root / "manifest.env").is_file())
            self.assertFalse((skill_root / "agents").exists())

    def test_codex_projects_optional_openai_metadata(self) -> None:
        result = self.package("codex", "beta")

        self.assertEqual(result.skills, ("alpha", "beta"))
        for skill_id in result.skills:
            skill_root = self.output / ".agents" / "skills" / skill_id
            self.assertTrue((skill_root / "SKILL.md").is_file())
            self.assertTrue((skill_root / "agents" / "openai.yaml").is_file())

    def test_claude_ai_zip_is_deterministic_and_has_one_top_level_folder(
        self,
    ) -> None:
        first = self.package("claude-ai", "beta")
        first_hashes = {
            artifact.output_path.name: sha256_file(artifact.output_path)
            for artifact in first.artifacts
        }
        second = self.package("claude-ai", "beta")
        second_hashes = {
            artifact.output_path.name: sha256_file(artifact.output_path)
            for artifact in second.artifacts
        }

        self.assertEqual(first_hashes, second_hashes)
        self.assertEqual(first.content_hash, second.content_hash)
        for artifact in second.artifacts:
            with zipfile.ZipFile(artifact.output_path) as archive:
                names = archive.namelist()
                roots = {name.split("/", 1)[0] for name in names}
                self.assertEqual(roots, {artifact.skill_id})
                self.assertIn(f"{artifact.skill_id}/SKILL.md", names)
                self.assertIn(f"{artifact.skill_id}/manifest.env", names)
                self.assertFalse(
                    any(
                        name.startswith(f"{artifact.skill_id}/agents/")
                        for name in names
                    )
                )
                self.assertIsNone(archive.testzip())

    def test_rejects_unsupported_harness(self) -> None:
        with self.assertRaisesRegex(ValueError, "harness no soportado"):
            self.package("generic", "beta")

    def test_cli_emits_stable_short_summary(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ADAPTER_ROOT / "run_skill_packaging.py"),
                "--repository-root",
                str(ROOT),
                "--catalog-root",
                str(self.catalog),
                "--output-root",
                str(self.output),
                "--harness",
                "claude-ai",
                "--skill",
                "beta",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        lines = completed.stdout.splitlines()
        self.assertEqual(lines[0], "HARNESS=claude-ai")
        self.assertEqual(lines[1], "SKILLS=alpha,beta")
        self.assertEqual(lines[2], "ARTIFACTS=2")
        self.assertRegex(lines[3], r"^CONTENT_HASH=[a-f0-9]{64}$")

    def package(self, harness_id: str, *skill_ids: str) -> PackagingResult:
        return package_skills(
            repository_root=ROOT,
            catalog_root=self.catalog,
            output_root=self.output,
            skill_ids=skill_ids,
            harness_id=harness_id,
        )

    def write_skill(self, skill_id: str, *, requires: str = "") -> None:
        skill_root = self.catalog / skill_id
        (skill_root / "agents").mkdir(parents=True)
        (skill_root / "SKILL.md").write_text(
            "---\n"
            f"name: {skill_id}\n"
            f"description: Empaquetar {skill_id} en una prueba portable.\n"
            "---\n\n"
            f"# {skill_id}\n",
            encoding="utf-8",
        )
        (skill_root / "manifest.env").write_text(
            'FORMAT_VERSION="1"\n'
            f'SKILL_ID="{skill_id}"\n'
            'SKILL_VERSION="1.0.0"\n'
            f'REQUIRES="{requires}"\n',
            encoding="utf-8",
        )
        (skill_root / "agents" / "openai.yaml").write_text(
            "interface:\n"
            f'  display_name: "{skill_id.title()}"\n'
            f'  short_description: "Probar {skill_id}"\n'
            f'  default_prompt: "Usa ${skill_id}."\n',
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()

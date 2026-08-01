from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"
sys.path.insert(0, str(ROOT / "adapters" / "reference_python"))

from lifecycle_core.envfile import load_env  # noqa: E402


class TemplateContractTests(unittest.TestCase):
    def test_every_env_template_uses_strict_keys(self) -> None:
        templates = tuple(sorted(TEMPLATES.rglob("*.env")))
        self.assertTrue(templates)
        for path in templates:
            values = load_env(path)
            self.assertTrue(values, path)
            self.assertTrue(all(key == key.strip() for key in values), path)

    def test_repository_template_has_the_minimal_portable_contract(self) -> None:
        values = load_env(TEMPLATES / "registry" / "repos" / "REPOSITORY.env")

        self.assertEqual(
            set(values),
            {
                "FORMAT_VERSION",
                "REPO_ID",
                "REMOTE_URL",
                "DEFAULT_BRANCH",
                "HARNESS",
                "SKILLS",
                "STATUS",
            },
        )
        self.assertIn(
            values["HARNESS"],
            {"generic", "claude-code", "claude-ai", "codex"},
        )
        self.assertIn(values["STATUS"], {"ACTIVE", "PAUSED"})

    def test_claim_template_contains_collision_inputs(self) -> None:
        values = load_env(TEMPLATES / "lifecycle" / "local" / "claims" / "CLAIM.env")

        self.assertTrue(
            {
                "ACTOR",
                "STATUS",
                "BASE_FINGERPRINT",
                "PATHS",
                "SYMBOLS",
                "CONTRACTS",
                "CRITERIA",
            }.issubset(values)
        )

    def test_phase_templates_record_authorship(self) -> None:
        observation = load_env(TEMPLATES / "lifecycle" / "changes" / "OBSERVATION.env")
        skill_state = load_env(
            TEMPLATES / "lifecycle" / "state" / "skills" / "SKILL.env"
        )

        self.assertEqual(observation["KIND"], "OBSERVATION")
        self.assertIn("AUTHOR", observation)
        self.assertIn("CONFIRMED_BY", observation)
        self.assertIn("ADOPTED_BY", skill_state)

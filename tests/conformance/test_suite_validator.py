from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "adapters" / "reference_python"))

from lifecycle_core.suite_validator import (  # noqa: E402
    SuiteValidationReport,
    require_valid_suite,
    validate_suite,
)


class SuiteValidatorTests(unittest.TestCase):
    def test_current_catalog_is_portable(self) -> None:
        report = validate_suite(ROOT / "skills")

        self.assertTrue(report.ok, report.issues)
        self.assertEqual(
            {manifest.skill_id for manifest in report.manifests},
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
        )

    def test_dependency_cycle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            _write_skill(catalog, "alpha", requires="beta@1.0.0")
            _write_skill(catalog, "beta", requires="alpha@1.0.0")

            report = validate_suite(catalog)

            self.assertIn("DEPENDENCY_CYCLE", _codes(report))
            with self.assertRaisesRegex(ValueError, "DEPENDENCY_CYCLE"):
                require_valid_suite(catalog)

    def test_missing_and_mismatched_dependencies_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            _write_skill(
                catalog,
                "alpha",
                requires="beta@2.0.0,missing@1.0.0",
            )
            _write_skill(catalog, "beta")

            report = validate_suite(catalog)

        self.assertIn("MISSING_DEPENDENCY", _codes(report))
        self.assertIn("DEPENDENCY_VERSION_MISMATCH", _codes(report))

    def test_compatible_newer_dependency_satisfies_requirement(self) -> None:
        # D-060: PATCH y MINOR son compatibles. Con pin exacto, publicar un
        # PATCH de una skill base dejaba el catálogo entero en FAIL.
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            _write_skill(catalog, "alpha", requires="beta@1.0.0")
            _write_skill(catalog, "beta", version="1.2.3")

            report = validate_suite(catalog)

        self.assertNotIn("DEPENDENCY_VERSION_MISMATCH", _codes(report))

    def test_older_available_dependency_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            _write_skill(catalog, "alpha", requires="beta@1.0.2")
            _write_skill(catalog, "beta", version="1.0.0")

            report = validate_suite(catalog)

        self.assertIn("DEPENDENCY_VERSION_MISMATCH", _codes(report))

    def test_todo_and_broken_local_reference_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            root = _write_skill(catalog, "alpha")
            (root / "SKILL.md").write_text(
                _skill_markdown("alpha")
                + "\nTODO: completar.\n"
                + "[Contrato requerido](references/missing.md)\n",
                encoding="utf-8",
            )

            report = validate_suite(catalog)

        self.assertIn("TODO_FOUND", _codes(report))
        self.assertIn("MISSING_REFERENCE", _codes(report))

    def test_reference_cannot_escape_skill_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            root = _write_skill(catalog, "alpha")
            (root / "SKILL.md").write_text(
                _skill_markdown("alpha") + "\n[Fuera](../../outside.md)\n",
                encoding="utf-8",
            )

            report = validate_suite(catalog)

        self.assertIn("REFERENCE_OUTSIDE_SKILL", _codes(report))

    def test_common_frontmatter_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "skills"
            root = _write_skill(catalog, "alpha")
            description = "x" * 201
            (root / "SKILL.md").write_text(
                (
                    "---\n"
                    "name: alpha\n"
                    f"description: {description}\n"
                    "extra: forbidden\n"
                    "---\n\n"
                    "# Alpha\n"
                ),
                encoding="utf-8",
            )

            report = validate_suite(catalog)

        self.assertIn("INVALID_SKILL", _codes(report))


def _write_skill(
    catalog: Path,
    skill_id: str,
    *,
    requires: str = "",
    version: str = "1.0.0",
) -> Path:
    root = catalog / skill_id
    root.mkdir(parents=True)
    (root / "manifest.env").write_text(
        (
            'FORMAT_VERSION="1"\n'
            f'SKILL_ID="{skill_id}"\n'
            f'SKILL_VERSION="{version}"\n'
            f'REQUIRES="{requires}"\n'
        ),
        encoding="utf-8",
    )
    (root / "SKILL.md").write_text(
        _skill_markdown(skill_id),
        encoding="utf-8",
    )
    return root


def _skill_markdown(skill_id: str) -> str:
    return (
        "---\n"
        f"name: {skill_id}\n"
        f"description: Validar {skill_id} cuando una prueba lo solicita.\n"
        "---\n\n"
        f"# {skill_id}\n"
    )


def _codes(report: SuiteValidationReport) -> set[str]:
    return {issue.code for issue in report.issues}

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONCEPTS = ROOT / "docs" / "concepts"
sys.path.insert(0, str(ROOT / "adapters" / "reference_python"))

from sextante.receipt_schema import REQUIRED_FIELDS  # noqa: E402


class DocumentationGateTests(unittest.TestCase):
    def test_every_concept_has_required_sections(self) -> None:
        required_labels = ("Qué es", "Cuándo", "Cómo", "No es", "Ejemplo")
        concept_files = sorted(
            path for path in CONCEPTS.glob("*.md") if path.name != "INDEX.md"
        )
        self.assertTrue(concept_files)
        for path in concept_files:
            content = path.read_text(encoding="utf-8")
            for label in required_labels:
                self.assertIn(f"**{label}:", content, f"{path}: falta {label}")

    def test_index_references_every_concept_once(self) -> None:
        index = (CONCEPTS / "INDEX.md").read_text(encoding="utf-8")
        linked_names = re.findall(r"\]\(([^)]+\.md)\)", index)
        expected_names = sorted(
            path.name for path in CONCEPTS.glob("*.md") if path.name != "INDEX.md"
        )
        self.assertEqual(sorted(linked_names), expected_names)
        self.assertEqual(len(linked_names), len(set(linked_names)))

    def test_portable_contract_names_every_required_receipt_field(self) -> None:
        contract = (
            ROOT / "skills" / "sextante" / "references" / "receipt-v1.md"
        ).read_text(encoding="utf-8")
        missing = sorted(
            field for field in REQUIRED_FIELDS if f"`{field}`" not in contract
        )

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()

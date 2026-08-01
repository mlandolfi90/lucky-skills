from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "adapters" / "reference_python"))

from sextante.envfile import canonical_env, load_env  # noqa: E402


class EnvFileTests(unittest.TestCase):
    def test_round_trip_preserves_spaces_without_interpolation(self) -> None:
        values = {
            "WORKSPACE_PATH": r"C:\Projects\Skills v3",
            "LITERAL": "${HOME}",
            "UNICODE": "Brújula",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "sample.env"
            path.write_text(canonical_env(values), encoding="utf-8")
            self.assertEqual(load_env(path), values)

    def test_rejects_invalid_keys(self) -> None:
        with self.assertRaises(ValueError):
            canonical_env({"bad-key": "value"})

    def test_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "duplicate.env"
            path.write_text('MODE="ONE"\nMODE="TWO"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_env(path)


if __name__ == "__main__":
    unittest.main()

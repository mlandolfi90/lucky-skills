from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from lifecycle_core.hashing import tree_hash  # noqa: E402
from lifecycle_core.manifest import Version  # noqa: E402
from lifecycle_core.paths import normalize_relative  # noqa: E402


class LifecycleCoreTests(unittest.TestCase):
    def test_version_satisfies_follows_semver_compatibility(self) -> None:
        required = Version.parse("1.0.0")
        self.assertTrue(Version.parse("1.0.0").satisfies(required))
        self.assertTrue(Version.parse("1.0.3").satisfies(required))
        self.assertTrue(Version.parse("1.2.0").satisfies(required))
        self.assertFalse(Version.parse("2.0.0").satisfies(required))
        self.assertFalse(Version.parse("0.9.9").satisfies(required))
        self.assertFalse(Version.parse("1.0.1").satisfies(Version.parse("1.0.2")))

    def test_relative_paths_allow_spaces_and_unicode(self) -> None:
        self.assertEqual(
            normalize_relative("skills/viejo módulo/regla.md"),
            Path("skills") / "viejo módulo" / "regla.md",
        )

    def test_relative_paths_reject_escape_and_windows_reserved_names(self) -> None:
        for value in ("../outside", "skills/CON/file", "skills/bad?.md"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_relative(value)

    @unittest.skipIf(os.name == "nt", "Windows no conserva el bit POSIX")
    def test_portable_tree_hash_ignores_executable_bit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            script = root / "tool"
            script.write_text("#!/bin/sh\n", encoding="utf-8", newline="\n")
            script.chmod(stat.S_IRUSR | stat.S_IWUSR)
            before = tree_hash(root)
            script.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            self.assertEqual(tree_hash(root), before)


if __name__ == "__main__":
    unittest.main()

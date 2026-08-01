from __future__ import annotations

import sys

from support import AdapterHarness
from sextante.command import run_command


class CommandBoundTests(AdapterHarness):
    def test_subprocess_output_is_bounded(self) -> None:
        result = run_command(
            [sys.executable, "-c", "print('x' * 100000)"],
            cwd=self.workspace,
            timeout_seconds=5,
            max_output_bytes=1024,
        )

        self.assertTrue(result.output_limited)
        self.assertEqual(result.returncode, 125)
        self.assertLessEqual(
            len(result.stdout.encode("utf-8")) + len(result.stderr.encode("utf-8")),
            1024,
        )

from __future__ import annotations

import os
import stat
from unittest.mock import patch

from support import AdapterHarness, state_map_fixture, write_utf8_lf
from sextante.local_probe import probe_local


class FingerprintTests(AdapterHarness):
    def test_touch_without_content_change_keeps_fingerprint(self) -> None:
        target = self.workspace / "stable.txt"
        target.write_text("stable", encoding="utf-8")
        original, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        original_times = target.stat()

        os.utime(
            target,
            ns=(original_times.st_atime_ns, original_times.st_mtime_ns + 1_000_000),
        )
        touched, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)

        self.assertEqual(original.fingerprint, touched.fingerprint)

    def test_same_size_change_with_restored_mtime_changes_fingerprint(self) -> None:
        target = self.workspace / "same-size.txt"
        target.write_text("AAAA", encoding="utf-8")
        original, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        timestamps = target.stat()

        target.write_text("BBBB", encoding="utf-8")
        os.utime(
            target,
            ns=(timestamps.st_atime_ns, timestamps.st_mtime_ns),
        )
        changed, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)

        self.assertEqual(target.stat().st_size, 4)
        self.assertEqual(target.stat().st_mtime_ns, timestamps.st_mtime_ns)
        self.assertNotEqual(original.fingerprint, changed.fingerprint)

    def test_posix_executable_bit_changes_dirty_but_not_fingerprint(self) -> None:
        # D-078: el modo no participa en la huella compartida; el gate de
        # permisos vive en dirty, donde el bit es observable.
        if os.name == "nt":
            self.skipTest("Windows no expone de forma fiable el bit ejecutable POSIX")
        self.init_committed_repository()
        target = self.workspace / "module.py"
        original, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        original_mode = stat.S_IMODE(target.stat().st_mode)
        target.chmod(original_mode | stat.S_IXUSR)
        if not target.stat().st_mode & stat.S_IXUSR:
            self.skipTest("el filesystem no permite observar el bit ejecutable")

        changed, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )

        self.assertFalse(original.dirty)
        self.assertTrue(changed.dirty)
        self.assertGreater(changed.dirty_count, 0)
        self.assertEqual(original.fingerprint, changed.fingerprint)

    def test_observed_executable_mode_participates_in_dirty_only(self) -> None:
        self.init_committed_repository()
        with patch(
            "sextante.file_fingerprint._working_tree_mode",
            return_value="100644",
        ):
            original, _ = probe_local(
                self.workspace,
                timeout_seconds=5,
                max_entries=100,
            )
        with patch(
            "sextante.file_fingerprint._working_tree_mode",
            return_value="100755",
        ):
            executable, _ = probe_local(
                self.workspace,
                timeout_seconds=5,
                max_entries=100,
            )

        self.assertTrue(executable.dirty)
        self.assertGreater(executable.dirty_count, 0)
        self.assertEqual(original.fingerprint, executable.fingerprint)

    def test_fingerprint_is_stable_across_branch_commit_and_merge(self) -> None:
        # El ciclo real de adopción: la skill aterriza sin trackear en una rama
        # de trabajo, sincronizar la commitea y el humano mergea a main. Si la
        # huella cambia en cualquiera de esos pasos sin que cambie un byte, el
        # STATE-MAP queda en DRIFT permanente y ningún sync posterior aplica.
        self.init_committed_repository()
        on_main, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)

        self.git("checkout", "-b", "codex/skills-demo-v1.0.0")
        same_tree, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        self.assertEqual(on_main.fingerprint, same_tree.fingerprint)

        skill = self.workspace / "skills" / "demo" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        # Las skills reales fijan su fin de línea (D-077); sin esto, un checkout
        # posterior reescribiría los bytes según la config de la máquina y el
        # cambio de huella sería un cambio real de contenido, no un falso drift.
        write_utf8_lf(skill.parent / ".gitattributes", "* text=auto eol=lf\n")
        write_utf8_lf(skill, "# demo\n")
        untracked, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        self.assertNotEqual(same_tree.fingerprint, untracked.fingerprint)

        self.git("add", "-A")
        self.git("commit", "-m", "sync skill")
        committed, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        self.assertEqual(untracked.fingerprint, committed.fingerprint)

        self.git("checkout", "main")
        self.git("merge", "--no-ff", "codex/skills-demo-v1.0.0", "-m", "merge")
        merged, _ = probe_local(self.workspace, timeout_seconds=5, max_entries=100)
        self.assertEqual(committed.fingerprint, merged.fingerprint)

    def test_state_map_self_fingerprint_is_stable_and_other_changes_are_not(
        self,
    ) -> None:
        self.init_committed_repository()
        initial_head = self.git("rev-parse", "HEAD").stdout.strip()
        state_map = self.workspace / ".lifecycle" / "state" / "STATE-MAP.env"
        state_map.parent.mkdir(parents=True)
        write_utf8_lf(
            state_map,
            state_map_fixture(local_commit=initial_head),
        )
        self.git("add", state_map.relative_to(self.workspace).as_posix())
        self.git("commit", "-m", "test: add state map")
        baseline, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )

        write_utf8_lf(
            state_map,
            state_map.read_text(encoding="utf-8").replace(
                'GIT_LOCAL_FINGERPRINT="UNKNOWN"',
                f'GIT_LOCAL_FINGERPRINT="{baseline.fingerprint}"',
            ),
        )
        working, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        self.assertEqual(baseline.fingerprint, working.fingerprint)
        self.assertTrue(working.dirty)

        self.git("add", state_map.relative_to(self.workspace).as_posix())
        staged, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        self.assertEqual(baseline.fingerprint, staged.fingerprint)

        self.git("commit", "-m", "test: record local fingerprint")
        committed, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        self.assertNotEqual(baseline.head, committed.head)
        self.assertEqual(baseline.fingerprint, committed.fingerprint)
        self.assertEqual(baseline.dirty, committed.dirty)

        write_utf8_lf(
            state_map,
            state_map.read_text(encoding="utf-8").replace(
                'STATE_REVISION="0"',
                'STATE_REVISION="1"',
            ),
        )
        changed_other_field, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        self.assertNotEqual(
            committed.fingerprint,
            changed_other_field.fingerprint,
        )

    def test_state_map_commit_can_lag_when_known_fingerprint_matches(self) -> None:
        self.init_committed_repository()
        base_commit = self.git("rev-parse", "HEAD").stdout.strip()
        state_map = self.workspace / ".lifecycle" / "state" / "STATE-MAP.env"
        state_map.parent.mkdir(parents=True)
        write_utf8_lf(
            state_map,
            state_map_fixture(local_commit=base_commit),
        )
        self.git("add", state_map.relative_to(self.workspace).as_posix())
        self.git("commit", "-m", "test: adopt state map")
        observed, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        write_utf8_lf(
            state_map,
            state_map.read_text(encoding="utf-8").replace(
                'GIT_LOCAL_FINGERPRINT="UNKNOWN"',
                f'GIT_LOCAL_FINGERPRINT="{observed.fingerprint}"',
            ),
        )
        self.git("add", state_map.relative_to(self.workspace).as_posix())
        self.git("commit", "-m", "test: record stable fingerprint")

        summary, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertEqual(summary["LOCAL"], "ALIGNED")
        self.assertEqual(receipt["LOCAL_FINGERPRINT"], observed.fingerprint)
        self.assertNotEqual(receipt["LOCAL_COMMIT"], base_commit)

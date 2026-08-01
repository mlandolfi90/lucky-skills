from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from change_lifecycle.records import (  # noqa: E402
    append_record,
    close_change,
    create_observation,
    record_autopsy,
    records,
)
from lifecycle_core.envfile import load_env  # noqa: E402
from lifecycle_core.receipts import verify_receipt  # noqa: E402


class ChangeLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / ".lifecycle" / "local").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_microfix_flow_records_each_author(self) -> None:
        observation = self._observation()
        change_id = load_env(observation)["CHANGE_ID"]
        diagnosis = append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="DIAGNOSIS",
            author="agent:diagnostic",
            confirmed_by="human:test",
            summary="cause found",
            evidence="test output",
        )
        microfix = append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="MICROFIX",
            author="session:mother:test",
            confirmed_by="human:test",
            summary="small fix",
            target_where="local:workspace",
            evidence="focused test passes",
            rollback="revert file",
        )
        closure = close_change(
            workspace=self.workspace,
            change_id=change_id,
            status="FINAL",
            result="behavior restored",
            author="session:mother:test",
            confirmed_by="human:test",
            tests="PASS",
            architecture="NOT_APPLICABLE",
            collision="NONE",
        )
        self.assertEqual(
            [load_env(path)["KIND"] for path in records(self.workspace, change_id)],
            ["OBSERVATION", "DIAGNOSIS", "MICROFIX", "CLOSURE"],
        )
        self.assertEqual(load_env(diagnosis)["AUTHOR"], "agent:diagnostic")
        self.assertTrue(verify_receipt(microfix))
        self.assertTrue(verify_receipt(closure))

    def test_writing_change_requires_target(self) -> None:
        change_id = load_env(self._observation())["CHANGE_ID"]
        append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="DIAGNOSIS",
            author="session:mother:test",
            confirmed_by="human:test",
            summary="cause",
        )
        with self.assertRaisesRegex(ValueError, "TARGET"):
            append_record(
                workspace=self.workspace,
                change_id=change_id,
                kind="HOTFIX",
                author="session:mother:test",
                confirmed_by="human:test",
                summary="urgent",
            )
        for invalid in ("", "UNKNOWN", "N/D", "NONE"):
            with self.subTest(target=invalid), self.assertRaisesRegex(
                ValueError,
                "TARGET",
            ):
                append_record(
                    workspace=self.workspace,
                    change_id=change_id,
                    kind="HOTFIX",
                    author="session:mother:test",
                    confirmed_by="human:test",
                    summary="urgent",
                    target_where=invalid,
                )

    def test_invalid_transition_is_rejected(self) -> None:
        change_id = load_env(self._observation())["CHANGE_ID"]
        with self.assertRaisesRegex(ValueError, "transición inválida"):
            append_record(
                workspace=self.workspace,
                change_id=change_id,
                kind="MICROFIX",
                author="session:mother:test",
                confirmed_by="human:test",
                summary="skipped diagnosis",
                target_where="local:workspace",
            )

    def test_final_closure_enforces_gates(self) -> None:
        change_id = self._diagnosed_change()
        with self.assertRaisesRegex(ValueError, "gates"):
            close_change(
                workspace=self.workspace,
                change_id=change_id,
                status="FINAL",
                result="not proven",
                author="session:mother:test",
                confirmed_by="human:test",
                tests="FAIL",
                architecture="PASS",
                collision="NONE",
            )

    def test_non_writing_observation_can_be_discarded_with_not_applicable_tests(
        self,
    ) -> None:
        change_id = load_env(self._observation())["CHANGE_ID"]
        closure = close_change(
            workspace=self.workspace,
            change_id=change_id,
            status="FINAL",
            result="observation discarded after review",
            author="session:mother:test",
            confirmed_by="human:test",
            tests="NOT_APPLICABLE",
            architecture="NOT_APPLICABLE",
            collision="NONE",
        )

        self.assertEqual(load_env(closure)["CLOSURE"], "FINAL")

    def test_conditional_closure_requires_an_explicit_condition(self) -> None:
        change_id = self._diagnosed_change()
        with self.assertRaisesRegex(ValueError, "conditions"):
            close_change(
                workspace=self.workspace,
                change_id=change_id,
                status="CONDITIONAL",
                result="useful but pending",
                author="session:mother:test",
                confirmed_by="human:test",
                tests="UNKNOWN",
                architecture="UNKNOWN",
                collision="UNKNOWN",
            )

    def test_autopsy_follows_execution_and_is_immutable(self) -> None:
        change_id = self._diagnosed_change()
        append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="HOTFIX",
            author="session:mother:test",
            confirmed_by="human:test",
            summary="restore",
            target_where="runtime:dev",
            rollback="previous image",
        )
        path = record_autopsy(
            workspace=self.workspace,
            change_id=change_id,
            author="agent:reviewer",
            confirmed_by="human:test",
            root_cause="bad condition",
            correction="condition fixed",
            recovery_evidence="health passes",
            prevention="add focused test",
        )
        self.assertTrue(verify_receipt(path))
        with self.assertRaisesRegex(ValueError, "transición inválida"):
            record_autopsy(
                workspace=self.workspace,
                change_id=change_id,
                author="agent:reviewer",
                confirmed_by="human:test",
                root_cause="again",
                correction="again",
                recovery_evidence="again",
                prevention="again",
            )

    def _observation(self) -> Path:
        return create_observation(
            workspace=self.workspace,
            summary="unexpected behavior",
            scope="LOCAL",
            author="human:test",
            confirmed_by="human:test",
            observed="500",
            expected="200",
        )

    def _diagnosed_change(self) -> str:
        change_id = load_env(self._observation())["CHANGE_ID"]
        append_record(
            workspace=self.workspace,
            change_id=change_id,
            kind="DIAGNOSIS",
            author="session:mother:test",
            confirmed_by="human:test",
            summary="cause",
        )
        return change_id


if __name__ == "__main__":
    unittest.main()

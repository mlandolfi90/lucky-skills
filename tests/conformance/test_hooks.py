from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ADAPTER_ROOT, ROOT

sys.path.insert(0, str(ADAPTER_ROOT))
sys.path.insert(
    0,
    str(ROOT / "skills" / "configurar-hooks" / "scripts"),
)

from lifecycle_hooks.contracts import (  # noqa: E402
    COMMON_EVENTS,
    EVENT_SCHEMA,
    HookEvent,
)
from lifecycle_hooks.dispatcher import (  # noqa: E402
    dispatch_event,
    verify_hook_receipt,
)
from lifecycle_hooks.normalizer import (  # noqa: E402
    host_response,
    normalize_host_event,
)
from lifecycle_core.envfile import load_env  # noqa: E402


def event(
    name: str,
    *,
    event_id: str = "event-1",
    harness: str = "test",
) -> HookEvent:
    return HookEvent(
        schema=EVENT_SCHEMA,
        event=name,
        event_id=event_id,
        harness=harness,
        workspace_id="sha256:" + ("a" * 64),
    )


class HookContractTests(unittest.TestCase):
    def test_contract_has_exactly_six_common_events(self) -> None:
        self.assertEqual(
            COMMON_EVENTS,
            (
                "SESSION_START",
                "BEFORE_WRITE",
                "AFTER_WRITE",
                "BEFORE_PUSH",
                "AFTER_FAILURE",
                "SESSION_END",
            ),
        )

    def test_event_rejects_arbitrary_payload_fields(self) -> None:
        values: dict[str, object] = {
            key: value for key, value in event("BEFORE_WRITE").to_mapping().items()
        }
        values["payload"] = {"secret": "must-not-be-accepted"}
        with self.assertRaisesRegex(ValueError, "campos no permitidos"):
            HookEvent.from_mapping(values)


class HookDispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.receipts = Path(self.temporary.name) / "receipts"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_repeat_is_idempotent_and_receipt_is_valid(self) -> None:
        first = dispatch_event(
            event("BEFORE_WRITE"),
            receipt_root=self.receipts,
        )
        second = dispatch_event(
            event("BEFORE_WRITE"),
            receipt_root=self.receipts,
        )
        self.assertEqual(first, second)
        files = list(self.receipts.glob("hook-*.json"))
        self.assertEqual(len(files), 1)
        self.assertTrue(verify_hook_receipt(files[0]))
        content = files[0].read_text(encoding="utf-8")
        self.assertNotIn("must-not-be-accepted", content)
        self.assertTrue(first.allow)
        self.assertEqual(first.mode, "ADVISORY")

    def test_event_id_conflict_is_rejected(self) -> None:
        dispatch_event(event("BEFORE_WRITE"), receipt_root=self.receipts)
        with self.assertRaisesRegex(ValueError, "event_id reutilizado"):
            dispatch_event(event("AFTER_WRITE"), receipt_root=self.receipts)

    def test_disabled_dispatcher_has_no_side_effect(self) -> None:
        result = dispatch_event(
            event("BEFORE_WRITE"),
            receipt_root=self.receipts,
            enabled=False,
        )
        self.assertEqual(result.status, "DISABLED")
        self.assertEqual(result.receipt, "")
        self.assertFalse(self.receipts.exists())

    def test_every_event_is_advisory_and_allows_continuation(self) -> None:
        for index, name in enumerate(COMMON_EVENTS):
            with self.subTest(event=name):
                result = dispatch_event(
                    event(name, event_id=f"event-{index}"),
                    receipt_root=self.receipts,
                )
                self.assertEqual(result.status, "OBSERVED")
                self.assertEqual(result.mode, "ADVISORY")
                self.assertTrue(result.allow)
                self.assertEqual(len(result.observations), 1)

    def test_json_cli_honors_environment_off_switch(self) -> None:
        script = ADAPTER_ROOT / "run_hooks.py"
        process_environment = dict(os.environ)
        process_environment["LIFECYCLE_HOOKS_ENABLED"] = "0"
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(script),
                "--receipt-root",
                str(self.receipts),
            ],
            input=json.dumps(event("SESSION_START").to_mapping()),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=process_environment,
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "DISABLED")
        self.assertIs(result["allow"], True)
        self.assertFalse(self.receipts.exists())


class HookHostAdapterTests(unittest.TestCase):
    def test_claude_code_maps_failure_and_git_push(self) -> None:
        workspace = Path.cwd()
        failure = normalize_host_event(
            harness="claude-code",
            declared_event="PostToolUseFailure",
            payload={"session_id": "s1", "tool_name": "Bash"},
            workspace=workspace,
        )
        push = normalize_host_event(
            harness="claude-code",
            declared_event="PreToolUse",
            payload={
                "session_id": "s1",
                "tool_use_id": "t1",
                "tool_name": "Bash",
                "tool_input": {"command": "git -C repo push origin main"},
            },
            workspace=workspace,
        )
        self.assertIsNotNone(failure)
        self.assertIsNotNone(push)
        assert failure is not None
        assert push is not None
        self.assertEqual(failure.event, "AFTER_FAILURE")
        self.assertEqual(push.event, "BEFORE_PUSH")

    def test_non_push_shell_command_is_ignored(self) -> None:
        observed = normalize_host_event(
            harness="codex",
            declared_event="PreToolUse",
            payload={
                "session_id": "s1",
                "tool_name": "shell",
                "tool_input": {"command": "git status"},
            },
            workspace=Path.cwd(),
        )
        self.assertIsNone(observed)

    def test_invalid_host_payload_fails_open(self) -> None:
        script = ROOT / "adapters" / "codex" / "hooks" / "run_hook.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(script), "SessionStart"],
            input="{not-json",
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        response = json.loads(completed.stdout)
        self.assertNotIn("continue", response)
        self.assertIn("systemMessage", response)
        self.assertNotIn("permissionDecision", response)

    def test_codex_response_uses_supported_advisory_output_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = dispatch_event(
                event("BEFORE_WRITE", harness="codex"),
                receipt_root=Path(temporary),
            )
            response = host_response(
                result,
                harness="codex",
                declared_event="PreToolUse",
            )

        self.assertEqual(set(response), {"systemMessage"})
        self.assertNotIn("hookSpecificOutput", response)
        self.assertNotIn("continue", response)

    def test_host_wrapper_observes_without_persisting_raw_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            receipts = base / "receipts"
            script = ROOT / "adapters" / "claude-code" / "hooks" / "run_hook.py"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(script),
                    "PreToolUse",
                    "--workspace",
                    str(base),
                    "--receipt-root",
                    str(receipts),
                ],
                input=json.dumps(
                    {
                        "session_id": "session-1",
                        "tool_use_id": "tool-1",
                        "tool_name": "Write",
                        "tool_input": {
                            "file_path": "private.txt",
                            "content": "DO-NOT-PERSIST",
                        },
                    }
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertIs(response["continue"], True)
            self.assertIn("additionalContext", response["hookSpecificOutput"])
            receipt_files = list(receipts.glob("hook-*.json"))
            self.assertEqual(len(receipt_files), 1)
            receipt_content = receipt_files[0].read_text(encoding="utf-8")
            self.assertNotIn("DO-NOT-PERSIST", receipt_content)
            self.assertNotIn("private.txt", receipt_content)
            self.assertTrue(verify_hook_receipt(receipt_files[0]))

    def test_runtime_inside_skill_is_standalone_after_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            installed = base / "skills" / "configurar-hooks" / "scripts"
            shutil.copytree(
                ROOT / "skills" / "configurar-hooks" / "scripts",
                installed,
            )
            receipts = base / ".lifecycle" / "local" / "hooks"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(installed / "run_hook.py"),
                    "codex",
                    "PreToolUse",
                    "--workspace",
                    str(base),
                    "--receipt-root",
                    str(receipts),
                ],
                input=json.dumps(
                    {
                        "session_id": "session-1",
                        "tool_use_id": "tool-1",
                        "tool_name": "apply_patch",
                        "cwd": str(base),
                    }
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=base,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(completed.stdout)
            self.assertEqual(set(response), {"systemMessage"})
            receipt_files = list(receipts.glob("hook-*.json"))
            self.assertEqual(len(receipt_files), 1)
            self.assertTrue(verify_hook_receipt(receipt_files[0]))

    def test_adapter_manifests_state_real_support(self) -> None:
        claude_code = load_env(
            ROOT / "adapters" / "claude-code" / "hooks" / "ADAPTER.env"
        )
        codex = load_env(ROOT / "adapters" / "codex" / "hooks" / "ADAPTER.env")
        claude_ai = load_env(ROOT / "adapters" / "claude-ai" / "hooks" / "ADAPTER.env")
        self.assertEqual(claude_code["HOOK_SUPPORT"], "SUPPORTED")
        self.assertEqual(codex["HOOK_SUPPORT"], "PARTIAL")
        self.assertEqual(codex["UNSUPPORTED_EVENTS"], "AFTER_FAILURE")
        self.assertEqual(claude_ai["HOOK_SUPPORT"], "UNSUPPORTED")
        self.assertEqual(claude_ai["CONFIG_TEMPLATE"], "NONE")
        self.assertEqual(claude_code["CONFIG_TARGET"], ".claude/settings.json")
        self.assertEqual(codex["CONFIG_TARGET"], ".codex/hooks.json")
        self.assertEqual(claude_ai["CONFIG_TARGET"], "NONE")
        self.assertEqual(
            claude_code["RUNTIME"],
            "skills/configurar-hooks/scripts/run_hook.py",
        )
        self.assertEqual(codex["RUNTIME"], claude_code["RUNTIME"])

    def test_templates_only_use_bounded_command_handlers(self) -> None:
        for harness in ("claude-code", "codex"):
            path = ROOT / "adapters" / harness / "hooks" / "hooks.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            for groups in config["hooks"].values():
                for group in groups:
                    for handler in group["hooks"]:
                        self.assertEqual(handler["type"], "command")
                        self.assertLessEqual(handler["timeout"], 5)
                        self.assertNotIn("enforce", handler["command"].lower())
                        self.assertNotIn("deny", handler["command"].lower())
                        serialized = json.dumps(handler)
                        self.assertIn(
                            "skills/configurar-hooks/scripts/run_hook.py",
                            serialized,
                        )
            if harness == "codex":
                session_end = config["hooks"]["Stop"][0]["hooks"][0]
                self.assertLessEqual(session_end["timeout"], 3)

    def test_templates_only_subscribe_to_events_the_host_emits(self) -> None:
        # Un evento que el host nunca emite instala un hook que jamás dispara y
        # declara una compatibilidad falsa. Codex cierra el turno con `Stop`; no
        # existe `SessionEnd`.
        host_events = {
            "claude-code": {
                "SessionStart",
                "UserPromptSubmit",
                "PreToolUse",
                "PostToolUse",
                "PostToolUseFailure",
                "SessionEnd",
            },
            "codex": {
                "SessionStart",
                "UserPromptSubmit",
                "PreToolUse",
                "PostToolUse",
                "PermissionRequest",
                "Stop",
                "PreCompact",
                "PostCompact",
                "SubagentStart",
                "SubagentStop",
            },
        }
        for harness, emitted in host_events.items():
            path = ROOT / "adapters" / harness / "hooks" / "hooks.json"
            config = json.loads(path.read_text(encoding="utf-8"))
            for declared_event in config["hooks"]:
                self.assertIn(
                    declared_event,
                    emitted,
                    f"{harness}: {declared_event} no es un evento del host",
                )


if __name__ == "__main__":
    unittest.main()

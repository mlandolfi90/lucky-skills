from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Mapping

from .contracts import EVENT_SCHEMA, HookEvent
from .dispatcher import DispatchResult


WRITE_TOOLS = frozenset(
    {
        "edit",
        "write",
        "multiedit",
        "notebookedit",
        "apply_patch",
        "functions.apply_patch",
    }
)
SHELL_TOOLS = frozenset(
    {
        "bash",
        "shell",
        "shell_command",
        "functions.shell_command",
        "exec_command",
    }
)
GIT_PUSH_PATTERN = re.compile(
    r"(?:^|[;&|]\s*)git"
    r"(?:\s+(?:-C|--git-dir|--work-tree)\s+\S+)*"
    r"\s+push(?:\s|$)",
    re.IGNORECASE,
)


def normalize_host_event(
    *,
    harness: str,
    declared_event: str,
    payload: Mapping[str, object],
    workspace: Path,
) -> HookEvent | None:
    common_event = _common_event(
        harness=harness,
        declared_event=declared_event,
        payload=payload,
    )
    if common_event is None:
        return None

    workspace_text = os.path.normcase(str(workspace.resolve()))
    workspace_id = (
        "sha256:" + hashlib.sha256(workspace_text.encode("utf-8")).hexdigest()
    )
    event_id = _event_id(
        harness=harness,
        declared_event=declared_event,
        common_event=common_event,
        payload=payload,
        workspace_id=workspace_id,
    )
    return HookEvent(
        schema=EVENT_SCHEMA,
        event=common_event,
        event_id=event_id,
        harness=harness,
        workspace_id=workspace_id,
    )


def host_response(
    result: DispatchResult | None,
    *,
    harness: str,
    declared_event: str,
) -> dict[str, object]:
    if result is None or result.status == "DISABLED":
        return {} if harness == "codex" else {"continue": True}
    context = "\n".join(result.observations)
    if harness == "codex":
        return {"systemMessage": context}
    if declared_event not in {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
    }:
        return {"continue": True, "systemMessage": context}
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": declared_event,
            "additionalContext": context,
        },
    }


def host_error_response(harness: str) -> dict[str, object]:
    message = (
        "El hook asesor omitió un evento inválido; " "la decisión humana se conserva."
    )
    if harness == "codex":
        return {"systemMessage": message}
    return {"continue": True, "systemMessage": message}


def _common_event(
    *,
    harness: str,
    declared_event: str,
    payload: Mapping[str, object],
) -> str | None:
    if declared_event == "SessionStart":
        return "SESSION_START"
    if declared_event in {"SessionEnd", "Stop"}:
        return "SESSION_END"

    tool_name = payload.get("tool_name", "")
    if not isinstance(tool_name, str):
        return None
    normalized_tool = tool_name.strip().lower()
    if declared_event == "PreToolUse":
        if normalized_tool in WRITE_TOOLS:
            return "BEFORE_WRITE"
        if normalized_tool in SHELL_TOOLS and _is_git_push(payload):
            return "BEFORE_PUSH"
        return None
    if declared_event == "PostToolUse" and normalized_tool in WRITE_TOOLS:
        return "AFTER_WRITE"
    if declared_event == "PostToolUseFailure" and harness == "claude-code":
        return "AFTER_FAILURE"
    return None


def _is_git_push(payload: Mapping[str, object]) -> bool:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    command = tool_input.get("command", "")
    return isinstance(command, str) and bool(GIT_PUSH_PATTERN.search(command))


def _event_id(
    *,
    harness: str,
    declared_event: str,
    common_event: str,
    payload: Mapping[str, object],
    workspace_id: str,
) -> str:
    identity_values: list[str] = []
    for key in ("tool_use_id", "session_id", "turn_id", "thread_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            identity_values.append(value[:256])
    seed = json.dumps(
        {
            "harness": harness,
            "declared_event": declared_event,
            "common_event": common_event,
            "workspace_id": workspace_id,
            "identities": identity_values,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return "host-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]

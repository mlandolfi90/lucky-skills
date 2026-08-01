from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .bounded_process import run_bounded_process


MAX_COMMAND_OUTPUT_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    output_limited: bool = False


def run_command(
    arguments: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    extra_env: dict[str, str] | None = None,
    sanitize_git_env: bool = False,
    max_output_bytes: int = MAX_COMMAND_OUTPUT_BYTES,
) -> CommandResult:
    environment = os.environ.copy()
    if sanitize_git_env:
        for key in tuple(environment):
            if key.upper().startswith("GIT_"):
                environment.pop(key, None)
    if extra_env:
        environment.update(extra_env)
    completed = run_bounded_process(
        arguments,
        cwd=cwd,
        environment=environment,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        timed_out=completed.timed_out,
        output_limited=completed.output_limited,
    )


class GitClient:
    """Run non-interactive Git queries with a per-command safe.directory fallback."""

    def __init__(self, workspace: Path, timeout_seconds: int) -> None:
        self.workspace = workspace.resolve()
        self.timeout_seconds = timeout_seconds
        self.safe_override = False
        self.available = True

    def query(self, *arguments: str) -> CommandResult:
        result = self._run(arguments, safe=self.safe_override)
        if _is_dubious_ownership(result):
            self.safe_override = True
            result = self._run(arguments, safe=True)
        if result.returncode == 127:
            self.available = False
        return result

    def _run(self, arguments: Sequence[str], *, safe: bool) -> CommandResult:
        command = [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.pager=cat",
            "-c",
            "pager.status=false",
            "-c",
            "submodule.recurse=false",
        ]
        if safe:
            command.extend(["-c", f"safe.directory={self.workspace.as_posix()}"])
        command.extend(["-C", str(self.workspace), *arguments])
        return run_command(
            command,
            cwd=self.workspace,
            timeout_seconds=self.timeout_seconds,
            extra_env={
                "GIT_TERMINAL_PROMPT": "0",
                "GCM_INTERACTIVE": "Never",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_NO_LAZY_FETCH": "1",
                "GIT_NO_REPLACE_OBJECTS": "1",
                "GIT_PAGER": "cat",
                "PAGER": "cat",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
            },
            sanitize_git_env=True,
        )


def _is_dubious_ownership(result: CommandResult) -> bool:
    return "dubious ownership" in result.stderr.lower()


def query_http_remote_ref(
    url: str,
    ref: str,
    *,
    timeout_seconds: int,
) -> CommandResult:
    """Query one exact HTTP(S) ref without redirects or ambient Git config."""
    command = [
        "git",
        "-c",
        "credential.helper=",
        "-c",
        "core.askPass=",
        "-c",
        "core.pager=cat",
        "-c",
        "protocol.allow=never",
        "-c",
        "protocol.http.allow=always",
        "-c",
        "protocol.https.allow=always",
        "-c",
        "http.extraHeader=",
        "-c",
        "http.cookieFile=",
        "-c",
        "http.saveCookies=false",
        "-c",
        "http.followRedirects=false",
        "ls-remote",
        "--exit-code",
        "--refs",
        url,
        ref,
    ]
    return run_command(
        command,
        cwd=Path(tempfile.gettempdir()).resolve(),
        timeout_seconds=timeout_seconds,
        extra_env={
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
        sanitize_git_env=True,
    )

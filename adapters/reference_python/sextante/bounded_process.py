from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


READ_CHUNK_BYTES = 64 * 1024


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    output_limited: bool


def run_bounded_process(
    arguments: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
    max_output_bytes: int,
) -> ProcessResult:
    try:
        process = subprocess.Popen(
            list(arguments),
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except OSError as error:
        return ProcessResult(127, "", str(error), False, False)
    assert process.stdout is not None
    assert process.stderr is not None

    chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
    total_bytes = 0
    lock = threading.Lock()
    output_limited = threading.Event()

    def drain(name: str, stream) -> None:
        nonlocal total_bytes
        while data := stream.read(READ_CHUNK_BYTES):
            with lock:
                remaining = max_output_bytes - total_bytes
                if remaining > 0:
                    kept = data[:remaining]
                    chunks[name].append(kept)
                    total_bytes += len(kept)
                if len(data) > remaining:
                    output_limited.set()
            if output_limited.is_set():
                try:
                    process.kill()
                except OSError:
                    pass
                break

    readers = tuple(
        threading.Thread(
            target=drain,
            args=(name, stream),
            daemon=True,
        )
        for name, stream in (
            ("stdout", process.stdout),
            ("stderr", process.stderr),
        )
    )
    for reader in readers:
        reader.start()

    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait()
    for reader in readers:
        reader.join()
    for stream in (process.stdout, process.stderr):
        stream.close()

    return ProcessResult(
        returncode=(
            124
            if timed_out
            else (125 if output_limited.is_set() else process.returncode)
        ),
        stdout=b"".join(chunks["stdout"]).decode("utf-8", errors="replace"),
        stderr=b"".join(chunks["stderr"]).decode("utf-8", errors="replace"),
        timed_out=timed_out,
        output_limited=output_limited.is_set(),
    )

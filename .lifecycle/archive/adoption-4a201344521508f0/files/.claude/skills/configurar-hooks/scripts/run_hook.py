from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from lifecycle_hooks.host_cli import main  # noqa: E402


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("uso: run_hook.py <harness> <evento> [opciones]")
    raise SystemExit(
        main(
            [
                "--harness",
                sys.argv[1],
                "--event",
                sys.argv[2],
                *sys.argv[3:],
            ]
        )
    )

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3] / "skills" / "configurar-hooks" / "scripts"
    ),
)

from lifecycle_hooks.host_cli import main  # type: ignore[import-not-found]  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--harness", "codex", "--event", *sys.argv[1:]]))

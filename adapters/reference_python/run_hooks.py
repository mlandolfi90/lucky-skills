import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2] / "skills" / "configurar-hooks" / "scripts"
    ),
)

from lifecycle_hooks.portable_cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

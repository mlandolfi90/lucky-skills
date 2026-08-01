import sys

sys.dont_write_bytecode = True

from sextante.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())

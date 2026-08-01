from __future__ import annotations

import sys
from pathlib import Path


CONFORMANCE_ROOT = Path(__file__).resolve().parent / "tests" / "conformance"
sys.path.insert(0, str(CONFORMANCE_ROOT))

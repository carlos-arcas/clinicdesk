from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.quality_gate_components.mypy_checks import run_mypy_blocking_scope


if __name__ == "__main__":
    raise SystemExit(run_mypy_blocking_scope())

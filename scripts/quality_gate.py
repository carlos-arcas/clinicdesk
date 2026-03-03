#!/usr/bin/env python3
"""Wrapper del quality gate para mantener compatibilidad de CLI."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.quality_gate_components.entrypoint import main


if __name__ == "__main__":
    raise SystemExit(main())

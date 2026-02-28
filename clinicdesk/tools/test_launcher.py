from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, set_run_context

_LOGGER = get_logger(__name__)


def _parse_summary(output: str) -> tuple[int, int]:
    passed = 0
    failed = 0

    passed_match = re.search(r"(\d+)\s+passed", output)
    failed_match = re.search(r"(\d+)\s+failed", output)

    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))

    return passed, failed


def main() -> int:
    configure_logging("clinicdesk-test-launcher", Path("./logs"), level="INFO", json=False)
    set_run_context("testlauncher")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        text=True,
        capture_output=True,
    )

    if result.stdout:
        _LOGGER.info(result.stdout.rstrip())
    if result.stderr:
        _LOGGER.error(result.stderr.rstrip())

    passed, failed = _parse_summary(result.stdout + result.stderr)
    total = passed + failed
    _LOGGER.info("Resumen tests: total=%s, passed=%s, failed=%s", total, passed, failed)

    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

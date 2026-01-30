from __future__ import annotations

import re
import subprocess
import sys


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
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    passed, failed = _parse_summary(result.stdout + result.stderr)
    total = passed + failed

    print(f"Resumen tests: total={total}, passed={passed}, failed={failed}")

    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

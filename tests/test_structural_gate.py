from __future__ import annotations

from pathlib import Path
import textwrap

from scripts.structural_gate import analyze_repo, load_thresholds


BASE_THRESHOLDS = {
    "max_file_loc": 10,
    "max_function_loc": 60,
    "max_class_loc": 200,
    "max_cc": 10,
    "max_avg_cc_per_file": 6,
    "max_hotspots": 0,
    "exclude_paths": ["app/ui/**", "tests/**", "migrations/**", "sql/**"],
    "allowlist": [],
}


def _write_file(base: Path, relative: str, content: str) -> None:
    path = base / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def test_cc_expected_for_control_flow(tmp_path: Path) -> None:
    _write_file(
        tmp_path,
        "clinicdesk/app/service.py",
        """
        def evaluate(items, flag_a, flag_b):
            if flag_a and flag_b:
                for item in items:
                    if item > 0 or item < -10:
                        return item
            return None
        """,
    )
    thresholds = dict(BASE_THRESHOLDS)
    thresholds["max_cc"] = 5

    result = analyze_repo(tmp_path, thresholds)
    cc_violation = next(violation for violation in result.violations if violation.kind == "function_cc")
    assert cc_violation.actual == 6


def test_loc_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    _write_file(
        tmp_path,
        "clinicdesk/app/service.py",
        """
        # file comment

        def one():
            # inside comment
            value = 1

            return value
        """,
    )
    thresholds = dict(BASE_THRESHOLDS)
    thresholds["max_file_loc"] = 2

    result = analyze_repo(tmp_path, thresholds)
    file_violation = next(violation for violation in result.violations if violation.kind == "file_loc")
    assert file_violation.actual == 3


def test_detects_function_loc_violation(tmp_path: Path) -> None:
    body = "\n".join([f"    total += {index}" for index in range(65)])
    _write_file(tmp_path, "clinicdesk/app/large.py", f"def long_fn():\n    total = 0\n{body}\n    return total")

    result = analyze_repo(tmp_path, dict(BASE_THRESHOLDS))
    assert any(violation.kind == "function_loc" for violation in result.violations)


def test_respects_exclusions(tmp_path: Path) -> None:
    _write_file(tmp_path, "app/ui/heavy.py", "def heavy():\n    return 1")
    _write_file(tmp_path, "clinicdesk/app/core.py", "def core():\n    return 2")

    result = analyze_repo(tmp_path, dict(BASE_THRESHOLDS))
    assert result.files_scanned == 1


def test_allowlist_overrides_are_applied(tmp_path: Path) -> None:
    body = "\n".join([f"    total += {index}" for index in range(70)])
    _write_file(tmp_path, "clinicdesk/app/legacy.py", f"def legacy_fn():\n    total = 0\n{body}\n    return total")

    config_path = tmp_path / "thresholds.json"
    config_path.write_text(
        """
{
  "max_file_loc": 50,
  "max_function_loc": 60,
  "max_class_loc": 200,
  "max_cc": 10,
  "max_avg_cc_per_file": 6,
  "max_hotspots": 0,
  "exclude_paths": ["app/ui/**", "tests/**", "migrations/**", "sql/**"],
  "allowlist": [
    {
      "path": "clinicdesk/app/legacy.py",
      "max_function_loc": 100,
      "reason": "deuda temporal"
    }
  ]
}
""",
        encoding="utf-8",
    )

    thresholds = load_thresholds(config_path)
    result = analyze_repo(tmp_path, thresholds)
    assert not any(violation.kind == "function_loc" and not violation.allowlisted for violation in result.violations)
    assert any(violation.path.name == "legacy.py" and violation.allowlisted for violation in result.violations)

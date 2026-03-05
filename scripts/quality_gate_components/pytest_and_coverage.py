from __future__ import annotations

import logging
import os
import trace
from pathlib import Path
from typing import Iterable

import pytest

from . import config

_LOGGER = logging.getLogger(__name__)


def iter_core_files(core_paths: list[Path] | None = None) -> Iterable[Path]:
    return (path for path in (core_paths or config.CORE_PATHS) if path.exists())


def run_pytest_with_trace(pytest_args: list[str]) -> tuple[int, trace.Trace]:
    # Root cause CI: pytest-qt entraba por autoload de entrypoints aunque el selector fuera "not ui".
    original_addopts = os.environ.get("PYTEST_ADDOPTS")
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ["PYTEST_ADDOPTS"] = ""
    tracer = trace.Trace(count=True, trace=False)
    try:
        exit_code = tracer.runfunc(pytest.main, pytest_args)
    finally:
        if original_addopts is None:
            os.environ.pop("PYTEST_ADDOPTS", None)
        else:
            os.environ["PYTEST_ADDOPTS"] = original_addopts
        os.environ.pop("PYTEST_DISABLE_PLUGIN_AUTOLOAD", None)
    return int(exit_code), tracer


def compute_core_coverage(tracer: trace.Trace, core_paths: list[Path] | None = None) -> float:
    counts = tracer.results().counts
    executable_total = 0
    executed_total = 0
    for file_path in iter_core_files(core_paths=core_paths):
        executable = trace._find_executable_linenos(str(file_path))  # noqa: SLF001
        executable_total += len(executable)
        executed_total += sum(1 for line in executable if counts.get((str(file_path), line), 0) > 0)
    if executable_total == 0:
        return 0.0
    return (executed_total / executable_total) * 100.0


def _render_class_entry(file_path: Path, counts: dict[tuple[str, int], int], repo_root: Path) -> str:
    executable = sorted(trace._find_executable_linenos(str(file_path)))  # noqa: SLF001
    if not executable:
        return ""
    covered = sum(1 for line in executable if counts.get((str(file_path), line), 0) > 0)
    line_rate = covered / len(executable)
    rel_path = file_path.relative_to(repo_root).as_posix()
    lines = [
        f'<line number="{line}" hits="{1 if counts.get((str(file_path), line), 0) > 0 else 0}"/>' for line in executable
    ]
    return "".join(
        [
            f'<class name="{file_path.stem}" filename="{rel_path}" line-rate="{line_rate:.4f}" branch-rate="0">',
            "<methods/>",
            "<lines>",
            *lines,
            "</lines>",
            "</class>",
        ]
    )


def run_coverage_report(
    tracer: trace.Trace,
    coverage: float,
    coverage_xml_path: Path | None = None,
    repo_root: Path | None = None,
    core_paths: list[Path] | None = None,
) -> int:
    xml_path = coverage_xml_path or config.COVERAGE_XML_PATH
    root = repo_root or config.REPO_ROOT
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    counts = tracer.results().counts
    package_entries = [
        _render_class_entry(file_path, counts, root) for file_path in iter_core_files(core_paths=core_paths)
    ]
    xml_content = "".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<coverage line-rate="{coverage / 100:.4f}" branch-rate="0" version="clinicdesk-quality-gate">',
            "<sources><source>.</source></sources>",
            '<packages><package name="core" line-rate="0" branch-rate="0"><classes>',
            *(entry for entry in package_entries if entry),
            "</classes></package></packages>",
            "</coverage>",
        ]
    )
    xml_path.write_text(xml_content, encoding="utf-8")
    _LOGGER.info("[quality-gate] coverage.xml generado en %s", xml_path.relative_to(root))
    return 0

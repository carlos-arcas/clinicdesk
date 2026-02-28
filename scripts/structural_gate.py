#!/usr/bin/env python3
"""Structural quality gate (LOC + CC + hotspots)."""

from __future__ import annotations

import ast
import json
import logging
from itertools import chain
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from scripts.structural_report import render_report

DEFAULT_THRESHOLDS: dict[str, Any] = {
    "max_file_loc": 400,
    "max_function_loc": 60,
    "max_class_loc": 200,
    "max_cc": 10,
    "max_avg_cc_per_file": 6,
    "max_hotspots": 0,
    "exclude_paths": ["clinicdesk/app/ui/**", "clinicdesk/app/pages/**", "tests/**", "migrations/**", "sql/**"],
    "allowlist": [],
}


@dataclass(slots=True)
class AllowlistEntry:
    path: str
    max_cc: int | None = None
    max_function_loc: int | None = None
    max_class_loc: int | None = None
    max_file_loc: int | None = None
    max_avg_cc_per_file: float | None = None
    reason: str = ""


@dataclass(slots=True)
class FunctionMetric:
    name: str
    qualname: str
    loc: int
    cc: int
    lineno: int


@dataclass(slots=True)
class ClassMetric:
    name: str
    qualname: str
    loc: int
    lineno: int


@dataclass(slots=True)
class FileMetrics:
    path: Path
    file_loc: int
    functions: list[FunctionMetric]
    classes: list[ClassMetric]
    avg_cc: float
    max_cc: int
    file_score: float
    hotspot: bool
    allowlisted: bool
    allowlist_reason: str


@dataclass(slots=True)
class Violation:
    kind: str
    path: Path
    symbol: str
    actual: float
    threshold: float
    allowlisted: bool
    reason: str


@dataclass(slots=True)
class StructuralGateResult:
    files_scanned: int
    violations: list[Violation]
    hotspots: list[FileMetrics]

    @property
    def blocking_violations(self) -> list[Violation]:
        return [violation for violation in self.violations if not violation.allowlisted]


def _count_code_loc(lines: list[str]) -> int:
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def _node_loc(node: ast.AST, source_lines: list[str]) -> int:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start)
    return _count_code_loc(source_lines[start - 1 : end])


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.cc = 1

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        self.cc += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self.cc += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:  # noqa: N802
        self.cc += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        self.cc += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        self.cc += len(node.handlers)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # noqa: N802
        self.cc += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:  # noqa: N802
        self.cc += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:  # noqa: N802
        self.cc += len(node.cases)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:  # noqa: N802
        self.cc += len(node.ifs)
        self.generic_visit(node)


def compute_cc(node: ast.AST) -> int:
    visitor = CyclomaticComplexityVisitor()
    visitor.visit(node)
    return visitor.cc


def _iter_python_files(repo_root: Path, exclude_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*.py"):
        rel = path.relative_to(repo_root).as_posix()
        if any(fnmatch(rel, pattern) for pattern in exclude_paths):
            continue
        files.append(path)
    return sorted(files)


def scan_files(repo_root: Path, exclude_paths: list[str]) -> list[Path]:
    return _iter_python_files(repo_root, exclude_paths)


def _build_allowlist(entries: list[dict[str, Any]]) -> list[AllowlistEntry]:
    allowlist: list[AllowlistEntry] = []
    for entry in entries:
        allowlist.append(
            AllowlistEntry(
                path=entry["path"],
                max_cc=entry.get("max_cc"),
                max_function_loc=entry.get("max_function_loc"),
                max_class_loc=entry.get("max_class_loc"),
                max_file_loc=entry.get("max_file_loc"),
                max_avg_cc_per_file=entry.get("max_avg_cc_per_file"),
                reason=entry.get("reason", ""),
            )
        )
    return allowlist


def _find_allowlist(path: Path, repo_root: Path, allowlist: list[AllowlistEntry]) -> AllowlistEntry | None:
    rel = path.relative_to(repo_root).as_posix()
    for entry in allowlist:
        if fnmatch(rel, entry.path):
            return entry
    return None


def _file_metrics(path: Path) -> tuple[int, list[FunctionMetric], list[ClassMetric]]:
    source = path.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    tree = ast.parse(source)

    functions: list[FunctionMetric] = []
    classes: list[ClassMetric] = []

    class StackVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
            qualname = ".".join([*self.scope, node.name]) if self.scope else node.name
            classes.append(ClassMetric(name=node.name, qualname=qualname, loc=_node_loc(node, source_lines), lineno=node.lineno))
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
            qualname = ".".join([*self.scope, node.name]) if self.scope else node.name
            functions.append(
                FunctionMetric(
                    name=node.name,
                    qualname=qualname,
                    loc=_node_loc(node, source_lines),
                    cc=compute_cc(node),
                    lineno=node.lineno,
                )
            )
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
            qualname = ".".join([*self.scope, node.name]) if self.scope else node.name
            functions.append(
                FunctionMetric(
                    name=node.name,
                    qualname=qualname,
                    loc=_node_loc(node, source_lines),
                    cc=compute_cc(node),
                    lineno=node.lineno,
                )
            )
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

    StackVisitor().visit(tree)
    return _count_code_loc(source_lines), functions, classes


def analyze_file(
    path: Path,
    max_file_loc_threshold: float,
    max_cc_threshold: float,
) -> tuple[int, list[FunctionMetric], list[ClassMetric], int, float, float, bool]:
    file_loc, functions, classes = _file_metrics(path)
    max_function_cc = max((function.cc for function in functions), default=0)
    avg_cc = sum(function.cc for function in functions) / len(functions) if functions else 0.0
    file_score = (file_loc / max_file_loc_threshold) * 0.4 + (max_function_cc / max_cc_threshold) * 0.6
    hotspot = (
        file_score > 1.0
        or file_loc > max_file_loc_threshold
        or max_function_cc > max_cc_threshold
    )
    return file_loc, functions, classes, max_function_cc, avg_cc, file_score, hotspot


def _resolve_limit(allow: AllowlistEntry | None, key: str, default: float) -> float:
    value = getattr(allow, key) if allow else None
    return float(value) if value is not None else float(default)


def _resolve_limits(allow: AllowlistEntry | None, thresholds: dict[str, Any]) -> dict[str, float]:
    return {
        "max_file_loc": _resolve_limit(allow, "max_file_loc", thresholds["max_file_loc"]),
        "max_function_loc": _resolve_limit(allow, "max_function_loc", thresholds["max_function_loc"]),
        "max_class_loc": _resolve_limit(allow, "max_class_loc", thresholds["max_class_loc"]),
        "max_cc": _resolve_limit(allow, "max_cc", thresholds["max_cc"]),
        "max_avg_cc_per_file": _resolve_limit(allow, "max_avg_cc_per_file", thresholds["max_avg_cc_per_file"]),
    }


def _file_level_violations(
    path: Path,
    file_loc: int,
    avg_cc: float,
    limits: dict[str, float],
    allowlisted: bool,
    allow_reason: str,
) -> list[Violation]:
    rules = [
        ("file_loc", "<file>", float(file_loc), float(limits["max_file_loc"])),
        ("avg_cc_per_file", "<file>", float(avg_cc), float(limits["max_avg_cc_per_file"])),
    ]
    return [
        Violation(kind, path, symbol, actual, threshold, allowlisted, allow_reason)
        for kind, symbol, actual, threshold in rules
        if actual > threshold
    ]


def _function_violations(
    path: Path,
    functions: list[FunctionMetric],
    limits: dict[str, float],
    allowlisted: bool,
    allow_reason: str,
) -> list[Violation]:
    return [
        Violation(kind, path, function.qualname, actual, threshold, allowlisted, allow_reason)
        for function in functions
        for kind, actual, threshold in (
            ("function_loc", float(function.loc), float(limits["max_function_loc"])),
            ("function_cc", float(function.cc), float(limits["max_cc"])),
        )
        if actual > threshold
    ]


def _class_violations(
    path: Path,
    classes: list[ClassMetric],
    limits: dict[str, float],
    allowlisted: bool,
    allow_reason: str,
) -> list[Violation]:
    return [
        Violation(
            "class_loc",
            path,
            class_metric.qualname,
            float(class_metric.loc),
            float(limits["max_class_loc"]),
            allowlisted,
            allow_reason,
        )
        for class_metric in classes
        if class_metric.loc > limits["max_class_loc"]
    ]


def apply_thresholds(
    path: Path,
    repo_root: Path,
    thresholds: dict[str, Any],
    analyzed: tuple[int, list[FunctionMetric], list[ClassMetric], int, float, float, bool],
) -> tuple[FileMetrics, list[Violation]]:
    file_loc, functions, classes, max_cc, avg_cc, file_score, hotspot = analyzed
    allow = _find_allowlist(path, repo_root, thresholds["allowlist"])
    allowlisted = allow is not None
    allow_reason = allow.reason if allow else ""
    limits = _resolve_limits(allow, thresholds)

    metric = FileMetrics(
        path=path,
        file_loc=file_loc,
        functions=functions,
        classes=classes,
        avg_cc=avg_cc,
        max_cc=max_cc,
        file_score=file_score,
        hotspot=hotspot,
        allowlisted=allowlisted,
        allowlist_reason=allow_reason,
    )
    violations = list(
        chain(
            _file_level_violations(path, file_loc, avg_cc, limits, allowlisted, allow_reason),
            _function_violations(path, functions, limits, allowlisted, allow_reason),
            _class_violations(path, classes, limits, allowlisted, allow_reason),
        )
    )
    return metric, violations


def compute_hotspots(metrics: list[FileMetrics]) -> list[FileMetrics]:
    return sorted((metric for metric in metrics if metric.hotspot), key=lambda item: item.file_score, reverse=True)


def load_thresholds(config_path: Path | None) -> dict[str, Any]:
    merged = dict(DEFAULT_THRESHOLDS)
    if config_path and config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        merged.update(loaded)
    merged["allowlist"] = _build_allowlist(merged.get("allowlist", []))
    return merged


def analyze_repo(repo_root: Path, thresholds: dict[str, Any]) -> StructuralGateResult:
    files = scan_files(repo_root, thresholds["exclude_paths"])
    violations: list[Violation] = []
    metrics: list[FileMetrics] = []

    for path in files:
        metric, file_violations = apply_thresholds(
            path,
            repo_root,
            thresholds,
            analyze_file(path, thresholds["max_file_loc"], thresholds["max_cc"]),
        )
        metrics.append(metric)
        violations.extend(file_violations)

    hotspots = compute_hotspots(metrics)
    return StructuralGateResult(files_scanned=len(files), violations=violations, hotspots=hotspots)



def generate_report(
    result: StructuralGateResult,
    thresholds: dict[str, Any],
    repo_root: Path,
    report_path: Path,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result, thresholds, repo_root), encoding="utf-8")


def run_structural_gate(
    repo_root: Path,
    thresholds_path: Path | None,
    mode: str,
    report_path: Path,
    logger: logging.Logger,
) -> int:
    thresholds = load_thresholds(thresholds_path)
    result = analyze_repo(repo_root, thresholds)
    generate_report(result, thresholds, repo_root, report_path)

    blocking_hotspots = [hotspot for hotspot in result.hotspots if not hotspot.allowlisted]
    hotspot_limit_exceeded = len(blocking_hotspots) > thresholds["max_hotspots"]
    strict_failed = bool(result.blocking_violations) or hotspot_limit_exceeded

    if strict_failed:
        offenders = [
            {
                "path": violation.path.relative_to(repo_root).as_posix(),
                "symbol": violation.symbol,
                "kind": violation.kind,
                "actual": round(violation.actual, 2),
                "threshold": round(violation.threshold, 2),
            }
            for violation in result.blocking_violations[:3]
        ]
        logger.error(
            "quality_gate_structural_failed violations=%s blocking_hotspots=%s offenders=%s",
            len(result.blocking_violations),
            len(blocking_hotspots),
            offenders,
        )

    logger.info(
        "[structural-gate] files=%s violations=%s blocking=%s hotspots=%s report=%s",
        result.files_scanned,
        len(result.violations),
        len(result.blocking_violations),
        len(result.hotspots),
        report_path,
    )

    if mode == "report-only":
        return 0
    if strict_failed:
        return 4
    return 0

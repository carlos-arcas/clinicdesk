#!/usr/bin/env python3
"""Structural quality gate (LOC + CC + hotspots)."""

from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLDS: dict[str, Any] = {
    "max_file_loc": 400,
    "max_function_loc": 60,
    "max_class_loc": 200,
    "max_cc": 10,
    "max_avg_cc_per_file": 6,
    "max_hotspots": 0,
    "exclude_paths": ["app/ui/**", "tests/**", "migrations/**", "sql/**"],
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


def load_thresholds(config_path: Path | None) -> dict[str, Any]:
    merged = dict(DEFAULT_THRESHOLDS)
    if config_path and config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        merged.update(loaded)
    merged["allowlist"] = _build_allowlist(merged.get("allowlist", []))
    return merged


def analyze_repo(repo_root: Path, thresholds: dict[str, Any]) -> StructuralGateResult:
    files = _iter_python_files(repo_root, thresholds["exclude_paths"])
    violations: list[Violation] = []
    metrics: list[FileMetrics] = []

    for path in files:
        file_loc, functions, classes = _file_metrics(path)
        max_cc = max((function.cc for function in functions), default=0)
        avg_cc = sum(function.cc for function in functions) / len(functions) if functions else 0.0

        allow = _find_allowlist(path, repo_root, thresholds["allowlist"])
        allowlisted = allow is not None
        allow_reason = allow.reason if allow else ""

        max_file_loc = allow.max_file_loc if allow and allow.max_file_loc is not None else thresholds["max_file_loc"]
        max_function_loc = (
            allow.max_function_loc if allow and allow.max_function_loc is not None else thresholds["max_function_loc"]
        )
        max_class_loc = allow.max_class_loc if allow and allow.max_class_loc is not None else thresholds["max_class_loc"]
        max_cc_allowed = allow.max_cc if allow and allow.max_cc is not None else thresholds["max_cc"]
        max_avg_cc = allow.max_avg_cc_per_file if allow and allow.max_avg_cc_per_file is not None else thresholds["max_avg_cc_per_file"]

        file_score = (file_loc / thresholds["max_file_loc"]) * 0.4 + (max_cc / thresholds["max_cc"]) * 0.6
        hotspot = file_score > 1.0 or file_loc > thresholds["max_file_loc"] or max_cc > thresholds["max_cc"]

        metrics.append(
            FileMetrics(
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
        )

        if file_loc > max_file_loc:
            violations.append(
                Violation("file_loc", path, "<file>", float(file_loc), float(max_file_loc), allowlisted, allow_reason)
            )
        if avg_cc > max_avg_cc:
            violations.append(
                Violation("avg_cc_per_file", path, "<file>", float(avg_cc), float(max_avg_cc), allowlisted, allow_reason)
            )

        for function in functions:
            if function.loc > max_function_loc:
                violations.append(
                    Violation(
                        "function_loc",
                        path,
                        function.qualname,
                        float(function.loc),
                        float(max_function_loc),
                        allowlisted,
                        allow_reason,
                    )
                )
            if function.cc > max_cc_allowed:
                violations.append(
                    Violation(
                        "function_cc",
                        path,
                        function.qualname,
                        float(function.cc),
                        float(max_cc_allowed),
                        allowlisted,
                        allow_reason,
                    )
                )

        for class_metric in classes:
            if class_metric.loc > max_class_loc:
                violations.append(
                    Violation(
                        "class_loc",
                        path,
                        class_metric.qualname,
                        float(class_metric.loc),
                        float(max_class_loc),
                        allowlisted,
                        allow_reason,
                    )
                )

    hotspots = sorted((metric for metric in metrics if metric.hotspot), key=lambda item: item.file_score, reverse=True)
    return StructuralGateResult(files_scanned=len(files), violations=violations, hotspots=hotspots)


def _format_violations(violations: list[Violation], repo_root: Path) -> list[str]:
    rows = []
    for violation in violations:
        rel = violation.path.relative_to(repo_root).as_posix()
        allow = "sí" if violation.allowlisted else "no"
        reason = f" ({violation.reason})" if violation.reason else ""
        rows.append(
            f"- `{rel}` :: `{violation.symbol}` -> {violation.actual:.2f} > {violation.threshold:.2f} "
            f"(allowlisted: {allow}{reason})"
        )
    return rows


def _group_violations(violations: list[Violation], kind: str) -> list[Violation]:
    return [item for item in violations if item.kind == kind]


def _worst_function(metric: FileMetrics) -> FunctionMetric | None:
    if not metric.functions:
        return None
    return sorted(metric.functions, key=lambda item: (item.cc, item.loc), reverse=True)[0]


def generate_report(
    result: StructuralGateResult,
    thresholds: dict[str, Any],
    repo_root: Path,
    report_path: Path,
) -> None:
    top_hotspots = result.hotspots[:10]
    lines: list[str] = [
        "# Structural Quality Report",
        "",
        "## 1) Resumen",
        f"- total_files_scanned: **{result.files_scanned}**",
        f"- violations_count: **{len(result.violations)}**",
        f"- blocking_violations_count: **{len(result.blocking_violations)}**",
        f"- top_hotspots: **{len(top_hotspots)}**",
        "",
        "### Umbrales aplicados",
        f"- max_file_loc: {thresholds['max_file_loc']}",
        f"- max_function_loc: {thresholds['max_function_loc']}",
        f"- max_class_loc: {thresholds['max_class_loc']}",
        f"- max_cc: {thresholds['max_cc']}",
        f"- max_avg_cc_per_file: {thresholds['max_avg_cc_per_file']}",
        f"- max_hotspots: {thresholds['max_hotspots']}",
        "",
        "## 2) Violaciones por tipo",
        "",
        "### Files over LOC",
    ]
    lines.extend(_format_violations(_group_violations(result.violations, "file_loc"), repo_root) or ["- Ninguna."])
    lines.extend(["", "### Functions over LOC"])
    lines.extend(_format_violations(_group_violations(result.violations, "function_loc"), repo_root) or ["- Ninguna."])
    lines.extend(["", "### Classes over LOC"])
    lines.extend(_format_violations(_group_violations(result.violations, "class_loc"), repo_root) or ["- Ninguna."])
    lines.extend(["", "### Functions over CC"])
    lines.extend(_format_violations(_group_violations(result.violations, "function_cc"), repo_root) or ["- Ninguna."])

    lines.extend(
        [
            "",
            "## 3) Hotspots (top 10)",
            "",
            "| file | file_loc | max_cc | avg_cc | worst_function | score | allowlisted? |",
            "| --- | ---: | ---: | ---: | --- | ---: | --- |",
        ]
    )

    for metric in top_hotspots:
        rel = metric.path.relative_to(repo_root).as_posix()
        worst = _worst_function(metric)
        if worst:
            worst_label = f"{worst.qualname} (cc={worst.cc}, loc={worst.loc})"
        else:
            worst_label = "n/a"
        allowlisted_label = "sí" if metric.allowlisted else "no"
        lines.append(
            f"| `{rel}` | {metric.file_loc} | {metric.max_cc} | {metric.avg_cc:.2f} | "
            f"{worst_label} | {metric.file_score:.2f} | {allowlisted_label} |"
        )

    if not top_hotspots:
        lines.append("| n/a | 0 | 0 | 0.00 | n/a | 0.00 | no |")

    lines.extend(["", "## 4) Recomendaciones automáticas", ""])
    if not top_hotspots:
        lines.append("- No hay hotspots activos.")
    else:
        for metric in top_hotspots:
            rel = metric.path.relative_to(repo_root).as_posix()
            worst = _worst_function(metric)
            symbol = worst.qualname if worst else "<module>"
            lines.append(
                f"- `{rel}` / `{symbol}`: extrae funciones puras para separar ramas condicionales y bajar CC."
            )
            lines.append(
                f"- `{rel}`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo."
            )
            lines.append(
                f"- `{rel}` / `{symbol}`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura."
            )

    if thresholds["allowlist"]:
        lines.extend(["", "## Allowlist / deuda controlada", ""])
        for entry in thresholds["allowlist"]:
            lines.append(
                f"- `{entry.path}` -> overrides: max_cc={entry.max_cc}, max_function_loc={entry.max_function_loc}, "
                f"max_class_loc={entry.max_class_loc}, max_file_loc={entry.max_file_loc}, "
                f"max_avg_cc_per_file={entry.max_avg_cc_per_file}; reason: {entry.reason or 'n/a'}"
            )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

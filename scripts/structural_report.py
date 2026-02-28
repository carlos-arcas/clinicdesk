from __future__ import annotations

from pathlib import Path
from typing import Any


def _format_violations(violations: list[Any], repo_root: Path) -> list[str]:
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


def _worst_function(metric: Any) -> Any | None:
    return max(metric.functions, key=lambda item: (item.cc, item.loc), default=None)


def _report_violation_sections(result: Any, repo_root: Path) -> list[str]:
    sections = [
        ("Files over LOC", "file_loc"),
        ("Functions over LOC", "function_loc"),
        ("Classes over LOC", "class_loc"),
        ("Functions over CC", "function_cc"),
    ]
    lines = ["", "## 2) Violaciones por tipo", ""]
    for title, kind in sections:
        lines.append(f"### {title}")
        grouped = [item for item in result.violations if item.kind == kind]
        lines.extend(_format_violations(grouped, repo_root) or ["- Ninguna."])
        lines.append("")
    lines.pop()
    return lines


def _report_hotspots(top_hotspots: list[Any], repo_root: Path) -> list[str]:
    lines = [
        "",
        "## 3) Hotspots (top 10)",
        "",
        "| file | file_loc | max_cc | avg_cc | worst_function | score | allowlisted? |",
        "| --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for metric in top_hotspots:
        rel = metric.path.relative_to(repo_root).as_posix()
        worst = _worst_function(metric)
        worst_label = f"{worst.qualname} (cc={worst.cc}, loc={worst.loc})" if worst else "n/a"
        allowlisted_label = "sí" if metric.allowlisted else "no"
        lines.append(
            f"| `{rel}` | {metric.file_loc} | {metric.max_cc} | {metric.avg_cc:.2f} | "
            f"{worst_label} | {metric.file_score:.2f} | {allowlisted_label} |"
        )
    return lines if top_hotspots else lines + ["| n/a | 0 | 0 | 0.00 | n/a | 0.00 | no |"]


def _report_recommendations(top_hotspots: list[Any], repo_root: Path) -> list[str]:
    lines = ["", "## 4) Recomendaciones automáticas", ""]
    if not top_hotspots:
        return lines + ["- No hay hotspots activos."]
    for metric in top_hotspots:
        rel = metric.path.relative_to(repo_root).as_posix()
        symbol = _worst_function(metric).qualname if _worst_function(metric) else "<module>"
        lines.extend(
            [
                f"- `{rel}` / `{symbol}`: extrae funciones puras para separar ramas condicionales y bajar CC.",
                f"- `{rel}`: divide el módulo en submódulos cohesivos por bounded context para reducir LOC del archivo.",
                f"- `{rel}` / `{symbol}`: introduce use cases/ports para desacoplar orquestación de detalles de infraestructura.",
            ]
        )
    return lines


def _report_allowlist(thresholds: dict[str, Any]) -> list[str]:
    if not thresholds["allowlist"]:
        return []
    lines = ["", "## Allowlist / deuda controlada", ""]
    for entry in thresholds["allowlist"]:
        lines.append(
            f"- `{entry.path}` -> overrides: max_cc={entry.max_cc}, max_function_loc={entry.max_function_loc}, "
            f"max_class_loc={entry.max_class_loc}, max_file_loc={entry.max_file_loc}, "
            f"max_avg_cc_per_file={entry.max_avg_cc_per_file}; reason: {entry.reason or 'n/a'}"
        )
    return lines


def render_report(result: Any, thresholds: dict[str, Any], repo_root: Path) -> str:
    top_hotspots = result.hotspots[:10]
    lines = [
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
    ]
    lines.extend(_report_violation_sections(result, repo_root))
    lines.extend(_report_hotspots(top_hotspots, repo_root))
    lines.extend(_report_recommendations(top_hotspots, repo_root))
    lines.extend(_report_allowlist(thresholds))
    return "\n".join(lines) + "\n"

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from clinicdesk.app.bootstrap_logging import configure_logging, set_run_context
from scripts.structural_gate import run_structural_gate
from scripts.check_changelog import check_changelog
from scripts.check_security_docs import check_security_docs

from . import config
from .basic_repo_checks import check_forbidden_artifacts, check_no_print_calls, check_secret_patterns
from .mypy_checks import run_mypy_blocking_scope, run_mypy_report
from .pii_guardrail import check_pii_logging_guardrail
from .requirements_pin_check import check_requirements_pinneados
from .pip_audit_check import run_pip_audit
from .pytest_and_coverage import compute_core_coverage, run_coverage_report, run_pytest_with_trace
from .ruff_checks import run_required_ruff_checks
from .secrets_scan_check import run_secrets_scan

_LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinicDesk quality gate")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Fail gate on structural violations (default).")
    mode.add_argument("--report-only", action="store_true", help="Generate structural report without blocking.")
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=config.REPO_ROOT / "scripts" / "quality_thresholds.json",
        help="Path to structural thresholds JSON file.",
    )
    return parser.parse_args()


def _run_pre_checks() -> int:
    for check in (
        check_no_print_calls,
        check_forbidden_artifacts,
        check_secret_patterns,
        check_requirements_pinneados,
        run_pip_audit,
        run_secrets_scan,
        check_pii_logging_guardrail,
    ):
        rc = check()
        if rc != 0:
            return rc
    return 0


def _run_docs_checks() -> int:
    docs_rc = check_security_docs(repo_root=config.REPO_ROOT)
    if docs_rc != 0:
        return docs_rc

    try:
        check_changelog(path=config.REPO_ROOT / "CHANGELOG.md", version=config.APP_VERSION)
    except ValueError as exc:
        _LOGGER.error("[quality-gate] ❌ CHANGELOG inválido: %s", exc)
        return 2
    except OSError as exc:
        _LOGGER.error("[quality-gate] ❌ No se pudo leer CHANGELOG.md: %s", exc)
        return 2
    return 0


def _run_test_and_coverage() -> int:
    pytest_args = ["-q", "-m", "not ui"]
    _LOGGER.info("[quality-gate] Ejecutando pytest: python -m pytest %s", " ".join(pytest_args))
    test_rc, tracer = run_pytest_with_trace(pytest_args)
    if test_rc != 0:
        _LOGGER.error("[quality-gate] ❌ pytest falló con código %s.", test_rc)
        return test_rc

    coverage = compute_core_coverage(tracer)
    _LOGGER.info("[quality-gate] Core coverage: %.2f%% (mínimo %.2f%%)", coverage, config.MIN_COVERAGE)
    if coverage < config.MIN_COVERAGE:
        _LOGGER.error("[quality-gate] ❌ Cobertura de core por debajo del umbral.")
        return 2

    report_rc = run_coverage_report(tracer=tracer, coverage=coverage)
    if report_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Falló la generación de coverage.xml en docs/.")
    return report_rc


def _run_post_static_checks() -> int:
    ruff_rc = run_required_ruff_checks()
    if ruff_rc != 0:
        return ruff_rc
    mypy_scope_rc = run_mypy_blocking_scope()
    if mypy_scope_rc != 0:
        _LOGGER.error("[quality-gate] ❌ mypy bloqueante falló sobre scripts/mypy_scope.txt.")
        return mypy_scope_rc
    mypy_report_rc = run_mypy_report()
    if mypy_report_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Falló la generación de docs/mypy_report.txt.")
    return mypy_report_rc


def main() -> int:
    args = parse_args()
    mode = "report-only" if args.report_only else "strict"

    configure_logging("clinicdesk-quality-gate", config.REPO_ROOT / "logs", level="INFO", json=False)
    set_run_context("qualitygate")

    for stage in (_run_pre_checks, _run_post_static_checks, _run_test_and_coverage, _run_docs_checks):
        rc = stage()
        if rc != 0:
            return rc

    structural_rc = run_structural_gate(
        repo_root=config.REPO_ROOT,
        thresholds_path=args.thresholds,
        mode=mode,
        report_path=config.REPO_ROOT / "docs" / "quality_report.md",
        logger=_LOGGER,
    )
    if structural_rc != 0:
        _LOGGER.error("[quality-gate] ❌ Structural gate falló en modo %s.", mode)
        return structural_rc

    _LOGGER.info("[quality-gate] ✅ Gate superado.")
    return 0

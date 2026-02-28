from __future__ import annotations

from pathlib import Path

from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, log_soft_exception, set_run_context
from clinicdesk.app.crash_handler import fatal_exception_handler


def test_configure_logging_creates_operational_log(tmp_path: Path) -> None:
    configure_logging("test-app", tmp_path, json=False)
    set_run_context("run-test")
    logger = get_logger("tests.logging")

    logger.info("hello operational")

    content = (tmp_path / "app.log").read_text(encoding="utf-8")
    assert "hello operational" in content
    assert "run_id=run-test" in content


def test_log_soft_exception_writes_soft_file(tmp_path: Path) -> None:
    configure_logging("test-app", tmp_path, json=False)
    set_run_context("run-soft")
    logger = get_logger("tests.logging")

    try:
        raise ValueError("esperable")
    except ValueError as exc:
        log_soft_exception(logger, exc, {"step": "validation"})

    content = (tmp_path / "crash_soft.log").read_text(encoding="utf-8")
    assert "soft_exception" in content
    assert "ValueError: esperable" in content


def test_fatal_hook_handler_writes_fatal_file(tmp_path: Path) -> None:
    configure_logging("test-app", tmp_path, json=False)
    set_run_context("run-fatal")
    logger = get_logger("tests.logging")
    handler = fatal_exception_handler(logger)

    try:
        raise RuntimeError("fatal")
    except RuntimeError as exc:
        handler(type(exc), exc, exc.__traceback__)

    content = (tmp_path / "crash_fatal.log").read_text(encoding="utf-8")
    assert "unhandled_exception" in content
    assert "RuntimeError: fatal" in content


def test_logging_redacts_pii_in_message(tmp_path: Path) -> None:
    configure_logging("test-app", tmp_path, json=False)
    set_run_context("run-redact")
    logger = get_logger("tests.logging")

    logger.info(
        "Paciente Juan Pérez email juan.perez@example.com dni 12345678 teléfono +54 11 5555 6666"
    )

    content = (tmp_path / "app.log").read_text(encoding="utf-8")
    assert "juan.perez@example.com" not in content
    assert "12345678" not in content
    assert "+54 11 5555 6666" not in content
    assert "***" in content


def test_logging_redacts_pii_in_exception_traceback(tmp_path: Path) -> None:
    configure_logging("test-app", tmp_path, json=False)
    set_run_context("run-redact-soft")
    logger = get_logger("tests.logging")

    try:
        raise ValueError("Error para Maria Lopez doc 87654321 email maria@example.com")
    except ValueError as exc:
        log_soft_exception(
            logger,
            exc,
            {"nombre": "Maria Lopez", "documento": "87654321", "email": "maria@example.com"},
        )

    content = (tmp_path / "crash_soft.log").read_text(encoding="utf-8")
    assert "87654321" not in content
    assert "maria@example.com" not in content
    assert "***" in content

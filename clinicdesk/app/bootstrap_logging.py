from __future__ import annotations

import contextvars
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from clinicdesk.app.common.log_redaction import redact_text, redact_value

_RUN_ID: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="-")
_USER: contextvars.ContextVar[str | None] = contextvars.ContextVar("user", default=None)
_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_SOFT_KEY = "is_soft_crash"
_FATAL_KEY = "is_fatal_crash"


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = _RUN_ID.get()
        record.user = _USER.get() or "-"
        record.request_id = _REQUEST_ID.get()
        return True


class _SoftCrashFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(getattr(record, _SOFT_KEY, False))


class _FatalCrashFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return bool(getattr(record, _FATAL_KEY, False) or record.levelno >= logging.CRITICAL)


class _ExcludeCrashFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not bool(getattr(record, _SOFT_KEY, False) or getattr(record, _FATAL_KEY, False))


class _StructuredFormatter(logging.Formatter):
    def __init__(self, *, json_mode: bool) -> None:
        super().__init__()
        self._json_mode = json_mode

    def format(self, record: logging.LogRecord) -> str:
        message = redact_text(record.getMessage())
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "run_id": getattr(record, "run_id", "-"),
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "user": getattr(record, "user", "-"),
        }
        if record.exc_info:
            payload["traceback"] = redact_text(self.formatException(record.exc_info))
        if self._json_mode:
            return json.dumps(payload, ensure_ascii=False)
        return " ".join(f"{key}={value}" for key, value in payload.items())


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        extra = kwargs.get("extra", {})
        merged = {"run_id": _RUN_ID.get(), "request_id": _REQUEST_ID.get(), "user": _USER.get() or "-", **extra}
        kwargs["extra"] = redact_value(merged)
        return redact_value(msg), kwargs


def configure_logging(app_name: str, log_dir: Path, level: str = "INFO", json: bool = True) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = _StructuredFormatter(json_mode=json)
    context_filter = _ContextFilter()

    console = logging.StreamHandler(stream=sys.__stderr__)
    console.setFormatter(formatter)
    console.addFilter(context_filter)
    console.addFilter(_ExcludeCrashFilter())

    app_file = RotatingFileHandler(log_dir / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    app_file.setFormatter(formatter)
    app_file.addFilter(context_filter)
    app_file.addFilter(_ExcludeCrashFilter())

    soft_file = RotatingFileHandler(log_dir / "crash_soft.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    soft_file.setFormatter(formatter)
    soft_file.addFilter(context_filter)
    soft_file.addFilter(_SoftCrashFilter())

    fatal_file = RotatingFileHandler(log_dir / "crash_fatal.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fatal_file.setFormatter(formatter)
    fatal_file.addFilter(context_filter)
    fatal_file.addFilter(_FatalCrashFilter())

    root_logger.addHandler(console)
    root_logger.addHandler(app_file)
    root_logger.addHandler(soft_file)
    root_logger.addHandler(fatal_file)
    logging.captureWarnings(True)
    get_logger(__name__).info("logging_configured", extra={"app_name": app_name})


def get_logger(name: str) -> logging.LoggerAdapter:
    return ContextLoggerAdapter(logging.getLogger(name), {})


def set_run_context(run_id: str, user: str | None = None) -> None:
    _RUN_ID.set(run_id)
    _USER.set(user)
    _REQUEST_ID.set(run_id)


def get_contexto_log() -> tuple[str, str]:
    return _RUN_ID.get(), _REQUEST_ID.get()


def log_soft_exception(logger: logging.LoggerAdapter, exc: Exception, context: dict[str, Any]) -> None:
    logger.error(
        "soft_exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={_SOFT_KEY: True, "context": context},
    )
    logger.error(
        "soft_exception_operational",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"context": context},
    )

from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from clinicdesk.app.common.log_redaction import redact_text

_RUN_ID: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="-")
_USER: contextvars.ContextVar[str | None] = contextvars.ContextVar("user", default=None)
_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_SOFT_KEY = "is_soft_crash"
_FATAL_KEY = "is_fatal_crash"


def _guardrail_pii_activo() -> bool:
    return os.getenv("CLINICDESK_LOG_PII", "0") != "1"


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


class _PIIRedactionFilter(logging.Filter):
    _TOKENS_SENSIBLES = ("dni", "nif", "email", "telefono", "teléfono", "direccion")
    _EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

    def __init__(self, *, permitir_pii: bool) -> None:
        super().__init__()
        self._permitir_pii = permitir_pii

    def filter(self, record: logging.LogRecord) -> bool:
        if self._permitir_pii:
            return True

        hubo_redaccion = False
        redacted_message = redact_text(record.getMessage())
        if redacted_message != record.getMessage():
            record.msg = redacted_message
            record.args = ()
            hubo_redaccion = True

        extra_publico = {
            key: value
            for key, value in record.__dict__.items()
            if key not in logging.LogRecord(None, None, "", 0, "", (), None).__dict__
        }
        extra_redactado = self._redactar_extra(extra_publico)
        if extra_redactado != extra_publico or any(self._es_clave_sensible(str(key)) for key in extra_publico):
            hubo_redaccion = True
            for key, value in extra_redactado.items():
                setattr(record, key, value)

        if hubo_redaccion:
            setattr(record, "reason_code", "pii_redacted")
        return True

    def _redactar_extra(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            redacted: dict[Any, Any] = {}
            for key, value in payload.items():
                if isinstance(key, str) and self._es_clave_sensible(key):
                    redacted[key] = "***"
                else:
                    redacted[key] = self._redactar_extra(value)
            return redacted
        if isinstance(payload, list):
            return [self._redactar_extra(item) for item in payload]
        if isinstance(payload, tuple):
            return tuple(self._redactar_extra(item) for item in payload)
        if isinstance(payload, str):
            if self._EMAIL_RE.search(payload):
                return redact_text(payload)
            return payload
        return payload

    def _es_clave_sensible(self, key: str) -> bool:
        lowered = key.lower()
        return any(token in lowered for token in self._TOKENS_SENSIBLES)


class _StructuredFormatter(logging.Formatter):
    def __init__(self, *, json_mode: bool) -> None:
        super().__init__()
        self._json_mode = json_mode

    def format(self, record: logging.LogRecord) -> str:
        message = redact_text(record.getMessage()) if _guardrail_pii_activo() else record.getMessage()
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
            "reason_code": getattr(record, "reason_code", "-"),
        }
        if record.exc_info:
            raw_traceback = self.formatException(record.exc_info)
            payload["traceback"] = redact_text(raw_traceback) if _guardrail_pii_activo() else raw_traceback
        if self._json_mode:
            return json.dumps(payload, ensure_ascii=False)
        return " ".join(f"{key}={value}" for key, value in payload.items())


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        extra = kwargs.get("extra", {})
        merged = {"run_id": _RUN_ID.get(), "request_id": _REQUEST_ID.get(), "user": _USER.get() or "-", **extra}
        kwargs["extra"] = merged
        return msg, kwargs


def configure_logging(app_name: str, log_dir: Path, level: str = "INFO", json: bool = True) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    for log_name in ("app.log", "crash_soft.log", "crash_fatal.log"):
        (log_dir / log_name).write_text("", encoding="utf-8")

    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = _StructuredFormatter(json_mode=json)
    context_filter = _ContextFilter()
    permitir_pii = not _guardrail_pii_activo()
    pii_filter = _PIIRedactionFilter(permitir_pii=permitir_pii)

    console = logging.StreamHandler(stream=sys.__stderr__)
    console.setFormatter(formatter)
    console.addFilter(context_filter)
    console.addFilter(pii_filter)
    console.addFilter(_ExcludeCrashFilter())

    app_file = RotatingFileHandler(log_dir / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    app_file.setFormatter(formatter)
    app_file.addFilter(context_filter)
    app_file.addFilter(pii_filter)
    app_file.addFilter(_ExcludeCrashFilter())

    soft_file = RotatingFileHandler(log_dir / "crash_soft.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    soft_file.setFormatter(formatter)
    soft_file.addFilter(context_filter)
    soft_file.addFilter(pii_filter)
    soft_file.addFilter(_SoftCrashFilter())

    fatal_file = RotatingFileHandler(log_dir / "crash_fatal.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fatal_file.setFormatter(formatter)
    fatal_file.addFilter(context_filter)
    fatal_file.addFilter(pii_filter)
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

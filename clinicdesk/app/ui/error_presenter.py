from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget

from clinicdesk.app.domain.exceptions import ValidationError

_LOGGER = logging.getLogger("clinicdesk.ui")


def _ensure_logger() -> logging.Logger:
    if _LOGGER.handlers:
        return _LOGGER

    base_dir = Path(__file__).resolve().parents[2]
    log_dir = base_dir / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "clinicdesk.log"

    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)

    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)
    return _LOGGER


def _normalize_context(context: Optional[str]) -> Optional[str]:
    if not context:
        return None
    return context.strip() or None


def present_error(parent: QWidget, exc: Exception, context: str | None = None) -> None:
    context_text = _normalize_context(context)

    if isinstance(exc, ValidationError):
        QMessageBox.warning(parent, "Validación", str(exc))
        return

    if isinstance(exc, ValueError) and "isoformat" in str(exc).lower():
        QMessageBox.warning(
            parent,
            "Validación",
            "Fecha de nacimiento: formato inválido. Usa AAAA-MM-DD (ej: 1987-04-23).",
        )
        return

    if isinstance(exc, sqlite3.IntegrityError):
        base_msg = "Ya existe un registro con este Documento."
        if context_text:
            base_msg = f"{base_msg}\n{context_text}"
        QMessageBox.warning(parent, "Validación", base_msg)
        return

    logger = _ensure_logger()
    logger.error("Error inesperado en UI", exc_info=exc)

    QMessageBox.critical(
        parent,
        "Error",
        "Ha ocurrido un error inesperado. Revisa los datos o consulta el log.",
    )

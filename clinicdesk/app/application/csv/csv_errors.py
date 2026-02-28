from __future__ import annotations

import logging
import sqlite3

from clinicdesk.app.domain.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CsvErrorMixin:
    def _format_row_error(self, exc: Exception) -> str:
        logger.exception("Error al importar fila CSV", exc_info=exc)
        if isinstance(exc, ValidationError):
            return str(exc)
        if self._is_isoformat_value_error(exc):
            return "fecha_nacimiento: formato inválido (AAAA-MM-DD)"
        if isinstance(exc, sqlite3.IntegrityError):
            return self._format_integrity_error(exc)
        if self._is_model_type_error(exc):
            return "Error interno del modelo Paciente (revisar definición/validación)."
        return "Error inesperado al importar la fila."

    def _is_isoformat_value_error(self, exc: Exception) -> bool:
        return isinstance(exc, ValueError) and "isoformat" in str(exc).lower()

    def _format_integrity_error(self, exc: sqlite3.IntegrityError) -> str:
        message = str(exc).lower()
        if "num_colegiado" in message:
            return "num_colegiado duplicado"
        if "tipo_documento" in message and "documento" in message:
            return "registro duplicado: (tipo_documento, documento) ya existe"
        return "registro duplicado"

    def _is_model_type_error(self, exc: Exception) -> bool:
        if not isinstance(exc, TypeError):
            return False
        message = str(exc).lower()
        return "super(type, obj)" in message or "unexpected keyword argument" in message

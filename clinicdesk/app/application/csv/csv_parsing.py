from __future__ import annotations

from datetime import date
from typing import Optional

from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.exceptions import ValidationError


class CsvParsingMixin:
    def _parse_tipo_documento(self, v: Optional[str]) -> TipoDocumento:
        return self._parse_enum(v, TipoDocumento, "tipo_documento obligatorio.", "tipo_documento inválido")

    def _parse_tipo_sala(self, v: Optional[str]) -> TipoSala:
        return self._parse_enum(v, TipoSala, "tipo (sala) obligatorio.", "tipo de sala inválido")

    def _parse_enum(self, raw: Optional[str], enum_type, empty_message: str, invalid_prefix: str):
        val = (raw or "").strip()
        if not val:
            raise ValidationError(empty_message)

        normalized = self._normalize_enum_token(val)
        mapping = {self._normalize_enum_token(item.value): item for item in enum_type}
        enum_value = mapping.get(normalized)
        if enum_value:
            return enum_value

        opciones = ", ".join(item.value for item in enum_type)
        raise ValidationError(f"{invalid_prefix}: {val}. Opciones válidas: {opciones}.")

    def _parse_date_optional(self, v: Optional[str]) -> Optional[date]:
        val = (v or "").strip()
        if not val:
            return None
        try:
            return date.fromisoformat(val)
        except ValueError as e:
            raise ValidationError("fecha_nacimiento: formato inválido (AAAA-MM-DD)") from e

    def _parse_bool_default(self, v: Optional[str], *, default: bool) -> bool:
        val = (v or "").strip().lower()
        if val == "":
            return default
        if val in ("1", "true", "t", "si", "sí", "yes", "y"):
            return True
        if val in ("0", "false", "f", "no", "n"):
            return False
        raise ValidationError(f"Valor booleano inválido: {v}")

    def _to_int(self, v: Optional[str]) -> Optional[int]:
        val = (v or "").strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError as e:
            raise ValidationError(f"Entero inválido: {v}") from e

    def _none_if_empty(self, v: Optional[str]) -> Optional[str]:
        val = (v or "").strip()
        return val if val else None

    def _normalize_enum_token(self, value: str) -> str:
        return value.strip().upper().replace(".", "").replace(" ", "")

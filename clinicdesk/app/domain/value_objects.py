"""Utilidades internas de dominio."""

from __future__ import annotations

from typing import Optional

from clinicdesk.app.domain.exceptions import ValidationError


def _strip_or_none(value: Optional[str]) -> Optional[str]:
    """Normaliza strings opcionales: devuelve None si queda vacío tras strip()."""
    if value is None:
        return None
    v = value.strip()
    return v if v else None


def _require_non_empty(value: str, field_name: str) -> str:
    """Exige string no vacío; lanza ValidationError si no cumple."""
    v = value.strip()
    if not v:
        raise ValidationError(f"Campo obligatorio: {field_name}.")
    return v


def _validate_email_basic(email: Optional[str]) -> None:
    """Validación básica de email (no pretende ser RFC completa)."""
    if email is None:
        return
    e = email.strip()
    if not e:
        return
    if "@" not in e or "." not in e:
        raise ValidationError("Email no parece válido.")


def _validate_phone_basic(phone: Optional[str]) -> None:
    """Validación básica de teléfono: numérico si se indica."""
    if phone is None:
        return
    t = phone.strip()
    if not t:
        return
    if not t.isdigit():
        raise ValidationError("Teléfono debe ser numérico si se indica.")


def _ensure_non_negative(value: int, field_name: str) -> None:
    """Exige entero >= 0; lanza ValidationError si no cumple."""
    if value < 0:
        raise ValidationError(f"{field_name} no puede ser negativo.")


def _ensure_positive_id(value: int, field_name: str) -> None:
    """Exige id > 0; lanza ValidationError si no cumple."""
    if value <= 0:
        raise ValidationError(f"{field_name} inválido.")


def _require_override_note(note: Optional[str]) -> str:
    """Exige nota de override con mínimo razonable para auditoría."""
    n = (note or "").strip()
    if len(n) < 5:
        raise ValidationError("Nota de override obligatoria (mínimo 5 caracteres).")
    return n

from __future__ import annotations

import os


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def field_protection_enabled() -> bool:
    primary = os.getenv("SECURITY_FIELD_PROTECTION_ENABLED")
    if primary is not None:
        return _is_enabled(primary)
    return _is_enabled(os.getenv("CLINICDESK_FIELD_CRYPTO", "0"))


def pacientes_field_crypto_enabled() -> bool:
    return field_protection_enabled()


def medicos_field_crypto_enabled() -> bool:
    return field_protection_enabled()


def personal_field_crypto_enabled() -> bool:
    return field_protection_enabled()


def validate_field_crypto_configuration() -> None:
    if not pacientes_field_crypto_enabled():
        return

    key = os.getenv("CLINICDESK_CRYPTO_KEY", "").strip()
    if key:
        return

    raise RuntimeError(
        "Se activó CLINICDESK_FIELD_CRYPTO=1 pero falta CLINICDESK_CRYPTO_KEY. "
        "Define la clave antes de iniciar ClinicDesk o desactiva SECURITY_FIELD_PROTECTION_ENABLED/CLINICDESK_FIELD_CRYPTO."
    )

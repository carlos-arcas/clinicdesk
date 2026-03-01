from __future__ import annotations

import os


def pacientes_field_crypto_enabled() -> bool:
    value = os.getenv("CLINICDESK_FIELD_CRYPTO", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def medicos_field_crypto_enabled() -> bool:
    value = os.getenv("CLINICDESK_FIELD_CRYPTO", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def personal_field_crypto_enabled() -> bool:
    value = os.getenv("CLINICDESK_FIELD_CRYPTO", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def validate_field_crypto_configuration() -> None:
    if not pacientes_field_crypto_enabled():
        return

    key = os.getenv("CLINICDESK_CRYPTO_KEY", "").strip()
    if key:
        return

    raise RuntimeError(
        "Se activó CLINICDESK_FIELD_CRYPTO=1 pero falta CLINICDESK_CRYPTO_KEY. "
        "Define la clave antes de iniciar ClinicDesk o desactiva CLINICDESK_FIELD_CRYPTO."
    )

from __future__ import annotations

import os


def pacientes_field_crypto_enabled() -> bool:
    value = os.getenv("CLINICDESK_FIELD_CRYPTO", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}

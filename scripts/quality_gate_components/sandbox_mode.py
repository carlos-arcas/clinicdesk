from __future__ import annotations

import os


def sandbox_mode_activo(entorno: dict[str, str] | None = None) -> bool:
    variables = os.environ if entorno is None else entorno
    return variables.get("CLINICDESK_SANDBOX_MODE") == "1"

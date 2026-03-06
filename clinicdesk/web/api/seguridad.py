from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


API_KEY_ENV = "CLINICDESK_API_KEY"


def validar_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    api_key_esperada = os.getenv(API_KEY_ENV)
    if not api_key_esperada:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API deshabilitada: define CLINICDESK_API_KEY para habilitar /api/*.",
        )
    if x_api_key != api_key_esperada:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key inválida.")

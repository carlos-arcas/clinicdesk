from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorFeedback:
    titulo_key: str
    mensaje_key: str
    detalle: str


def presentar_error_recuperable(error: object) -> ErrorFeedback:
    detalle = str(error).strip() or error.__class__.__name__
    return ErrorFeedback(
        titulo_key="ux.error.generic_title",
        mensaje_key="ux.error.retryable_message",
        detalle=detalle,
    )

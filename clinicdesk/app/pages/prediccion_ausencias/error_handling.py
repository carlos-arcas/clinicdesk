from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorEntrenamientoNormalizado:
    reason_code: str
    mensaje_i18n_key: str


def normalizar_error_entrenamiento(err: str | BaseException | None) -> ErrorEntrenamientoNormalizado:
    reason_code = _resolver_reason_code(err)
    if reason_code in {"dataset_insuficiente", "dataset_empty"}:
        return ErrorEntrenamientoNormalizado(reason_code=reason_code, mensaje_i18n_key="prediccion.entrenar.error.faltan_citas")
    return ErrorEntrenamientoNormalizado(reason_code=reason_code, mensaje_i18n_key="prediccion.entrenar.error.no_preparar")


def _resolver_reason_code(err: str | BaseException | None) -> str:
    if isinstance(err, str) and err.strip():
        return err.strip()
    return "unexpected_error"

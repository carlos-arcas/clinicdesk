from __future__ import annotations

from clinicdesk.app.pages.prediccion_ausencias.error_handling import normalizar_error_entrenamiento


def test_normalizar_error_entrenamiento_dataset_insuficiente() -> None:
    normalizado = normalizar_error_entrenamiento("dataset_insuficiente")
    assert normalizado.reason_code == "dataset_insuficiente"
    assert normalizado.mensaje_i18n_key == "prediccion.entrenar.error.faltan_citas"


def test_normalizar_error_entrenamiento_dataset_empty() -> None:
    normalizado = normalizar_error_entrenamiento("dataset_empty")
    assert normalizado.reason_code == "dataset_empty"
    assert normalizado.mensaje_i18n_key == "prediccion.entrenar.error.faltan_citas"


def test_normalizar_error_entrenamiento_default_unexpected() -> None:
    normalizado = normalizar_error_entrenamiento(None)
    assert normalizado.reason_code == "unexpected_error"
    assert normalizado.mensaje_i18n_key == "prediccion.entrenar.error.no_preparar"

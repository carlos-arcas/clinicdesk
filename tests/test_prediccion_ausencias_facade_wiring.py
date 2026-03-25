from __future__ import annotations


def test_facade_prediccion_ausencias_expone_resumen_entrenamiento(container) -> None:
    facade = container.prediccion_ausencias_facade

    resumen = facade.obtener_resumen_ultimo_entrenamiento_uc.ejecutar()

    assert hasattr(facade, "obtener_resumen_ultimo_entrenamiento_uc")
    assert resumen.disponible is False
    assert resumen.reason_code == "sin_metadata"


def test_facade_prediccion_ausencias_expone_historial_entrenamiento(container) -> None:
    facade = container.prediccion_ausencias_facade

    historial = facade.obtener_historial_entrenamientos_uc.ejecutar()

    assert hasattr(facade, "obtener_historial_entrenamientos_uc")
    assert historial == []

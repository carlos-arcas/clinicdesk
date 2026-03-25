from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import ResumenEntrenamientoModeloDTO
from clinicdesk.app.pages.prediccion_ausencias.coordinador_resumen_modelo import derivar_estado_calidad_modelo


def _resumen(*, accuracy: float | None, recall: float | None) -> ResumenEntrenamientoModeloDTO:
    return ResumenEntrenamientoModeloDTO(
        fecha_entrenamiento="2026-03-25T10:00:00+00:00",
        model_type="PredictorAusenciasBaseline",
        muestras_train=48,
        muestras_validacion=12,
        accuracy=accuracy,
        recall_no_show=recall,
    )


def test_calidad_modelo_verde() -> None:
    estado = derivar_estado_calidad_modelo(_resumen(accuracy=0.7, recall=0.65))

    assert estado.estado == "VERDE"


def test_calidad_modelo_amarillo() -> None:
    estado = derivar_estado_calidad_modelo(_resumen(accuracy=0.55, recall=0.45))

    assert estado.estado == "AMARILLO"


def test_calidad_modelo_rojo_si_metricas_faltan() -> None:
    estado = derivar_estado_calidad_modelo(_resumen(accuracy=None, recall=None))

    assert estado.estado == "ROJO"

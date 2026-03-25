from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import ResumenEntrenamientoModeloDTO
from clinicdesk.app.application.prediccion_ausencias.dtos import HistorialEntrenamientoModeloDTO
from clinicdesk.app.pages.prediccion_ausencias.coordinador_resumen_modelo import (
    derivar_estado_calidad_modelo,
    derivar_estado_tendencia_historial,
)


def _resumen(*, accuracy: float | None, recall: float | None) -> ResumenEntrenamientoModeloDTO:
    return ResumenEntrenamientoModeloDTO(
        disponible=True,
        reason_code=None,
        fecha_entrenamiento="2026-03-25T10:00:00+00:00",
        model_type="PredictorAusenciasBaseline",
        version="prediccion_ausencias_v1",
        citas_usadas=60,
        muestras_train=48,
        muestras_validacion=12,
        tasa_no_show_train=0.3,
        tasa_no_show_validacion=0.25,
        accuracy=accuracy,
        precision_no_show=0.6,
        recall_no_show=recall,
        f1_no_show=0.57,
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


def _historial(*, calidad: str) -> HistorialEntrenamientoModeloDTO:
    return HistorialEntrenamientoModeloDTO(
        fecha_entrenamiento="2026-03-25T10:00:00+00:00",
        model_type="PredictorAusenciasBaseline",
        version="prediccion_ausencias_v1",
        citas_usadas=60,
        muestras_train=48,
        muestras_validacion=12,
        accuracy=0.5,
        precision_no_show=0.5,
        recall_no_show=0.4,
        f1_no_show=0.5,
        calidad_ux=calidad,
        ganador_criterio="f1",
        baseline_f1=0.4,
        v2_f1=0.5,
    )


def test_estado_tendencia_alerta_roja_activa() -> None:
    estado = derivar_estado_tendencia_historial(
        [_historial(calidad="ROJO"), _historial(calidad="ROJO"), _historial(calidad="ROJO")]
    )

    assert estado.alerta_activa is True
    assert estado.alerta_i18n_key == "prediccion_ausencias.historial.alerta.rojo_activa"

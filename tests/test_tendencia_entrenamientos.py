from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import HistorialEntrenamientoModeloDTO
from clinicdesk.app.application.prediccion_ausencias.tendencia_entrenamientos import (
    TENDENCIA_EMPEORA,
    TENDENCIA_ESTABLE,
    TENDENCIA_MEJORA,
    TENDENCIA_NO_DISPONIBLE,
    calcular_resumen_tendencia_historial,
)


def _item(*, accuracy: float | None, recall: float | None, calidad: str) -> HistorialEntrenamientoModeloDTO:
    return HistorialEntrenamientoModeloDTO(
        fecha_entrenamiento="2026-03-25T10:00:00+00:00",
        model_type="PredictorAusenciasBaseline",
        version="prediccion_ausencias_v1",
        citas_usadas=60,
        muestras_train=48,
        muestras_validacion=12,
        accuracy=accuracy,
        precision_no_show=0.5,
        recall_no_show=recall,
        f1_no_show=0.5,
        calidad_ux=calidad,
        ganador_criterio="f1",
        baseline_f1=0.4,
        v2_f1=0.5,
    )


def test_tendencia_mejora() -> None:
    resultado = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.71, recall=0.63, calidad="AMARILLO"),
            _item(accuracy=0.68, recall=0.61, calidad="AMARILLO"),
        ]
    )

    assert resultado.tendencia_accuracy == TENDENCIA_MEJORA
    assert resultado.tendencia_recall_no_show == TENDENCIA_MEJORA


def test_tendencia_empeora() -> None:
    resultado = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.52, recall=0.39, calidad="ROJO"),
            _item(accuracy=0.61, recall=0.48, calidad="AMARILLO"),
        ]
    )

    assert resultado.tendencia_accuracy == TENDENCIA_EMPEORA
    assert resultado.tendencia_recall_no_show == TENDENCIA_EMPEORA


def test_tendencia_estable_con_tolerancia() -> None:
    resultado = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.601, recall=0.511, calidad="AMARILLO"),
            _item(accuracy=0.6, recall=0.51, calidad="AMARILLO"),
        ]
    )

    assert resultado.tendencia_accuracy == TENDENCIA_ESTABLE
    assert resultado.tendencia_recall_no_show == TENDENCIA_ESTABLE


def test_tendencia_no_disponible_si_faltan_corridas() -> None:
    resultado = calcular_resumen_tendencia_historial([_item(accuracy=0.6, recall=0.5, calidad="AMARILLO")])

    assert resultado.tendencia_accuracy == TENDENCIA_NO_DISPONIBLE
    assert resultado.tendencia_recall_no_show == TENDENCIA_NO_DISPONIBLE
    assert resultado.alerta_rojo_consecutivo is False


def test_alerta_activa_con_tres_rojos_consecutivos() -> None:
    resultado = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.4, recall=0.3, calidad="ROJO"),
            _item(accuracy=0.42, recall=0.31, calidad="ROJO"),
            _item(accuracy=0.39, recall=0.29, calidad="ROJO"),
        ]
    )

    assert resultado.alerta_rojo_consecutivo is True
    assert resultado.rojos_consecutivos == 3


def test_alerta_inactiva_si_no_hay_tres_rojos_consecutivos() -> None:
    resultado = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.4, recall=0.3, calidad="ROJO"),
            _item(accuracy=0.42, recall=0.31, calidad="ROJO"),
            _item(accuracy=0.61, recall=0.45, calidad="AMARILLO"),
        ]
    )

    assert resultado.alerta_rojo_consecutivo is False
    assert resultado.rojos_consecutivos == 2

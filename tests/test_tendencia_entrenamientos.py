from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import HistorialEntrenamientoModeloDTO
from clinicdesk.app.application.prediccion_ausencias.tendencia_entrenamientos import (
    ACCION_MONITORIZAR,
    ACCION_REENTRENAR,
    ACCION_REVISAR_DATOS,
    SIN_ACCION,
    TENDENCIA_EMPEORA,
    TENDENCIA_ESTABLE,
    TENDENCIA_MEJORA,
    TENDENCIA_NO_DISPONIBLE,
    calcular_resumen_tendencia_historial,
    derivar_recomendacion_operativa_monitor_ml,
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


def test_recomendacion_fuerte_alerta_activa_con_calidad_roja() -> None:
    resumen = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.4, recall=0.3, calidad="ROJO"),
            _item(accuracy=0.42, recall=0.31, calidad="ROJO"),
            _item(accuracy=0.39, recall=0.29, calidad="ROJO"),
        ]
    )

    recomendacion = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen, calidad_ultimo_entrenamiento="ROJO"
    )

    assert recomendacion.codigo == ACCION_REVISAR_DATOS
    assert recomendacion.es_fuerte is True


def test_recomendacion_suave_si_tendencia_empeora_sin_alerta() -> None:
    resumen = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.54, recall=0.41, calidad="AMARILLO"),
            _item(accuracy=0.63, recall=0.48, calidad="VERDE"),
        ]
    )

    recomendacion = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen, calidad_ultimo_entrenamiento="AMARILLO"
    )

    assert recomendacion.codigo == ACCION_MONITORIZAR
    assert recomendacion.es_fuerte is False


def test_recomendacion_sin_accion_en_mejora_estable_o_no_disponible() -> None:
    resumen_mejora = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.73, recall=0.62, calidad="VERDE"),
            _item(accuracy=0.69, recall=0.58, calidad="AMARILLO"),
        ]
    )
    resumen_no_disponible = calcular_resumen_tendencia_historial(
        [_item(accuracy=0.7, recall=0.6, calidad="VERDE")]
    )

    recomendacion_mejora = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen_mejora, calidad_ultimo_entrenamiento="VERDE"
    )
    recomendacion_no_disponible = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen_no_disponible, calidad_ultimo_entrenamiento=None
    )

    assert recomendacion_mejora.codigo == SIN_ACCION
    assert recomendacion_no_disponible.codigo == SIN_ACCION


def test_recomendacion_alerta_activa_sin_rojo_en_calidad_sugiere_reentrenar() -> None:
    resumen = calcular_resumen_tendencia_historial(
        [
            _item(accuracy=0.55, recall=0.42, calidad="ROJO"),
            _item(accuracy=0.54, recall=0.41, calidad="ROJO"),
            _item(accuracy=0.53, recall=0.4, calidad="ROJO"),
        ]
    )

    recomendacion = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen, calidad_ultimo_entrenamiento="AMARILLO"
    )

    assert recomendacion.codigo == ACCION_REENTRENAR

from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import ResumenEntrenamientoModeloDTO
from clinicdesk.app.application.prediccion_ausencias.dtos import HistorialEntrenamientoModeloDTO
from clinicdesk.app.pages.prediccion_ausencias.coordinador_resumen_modelo import (
    DedupeTelemetriaMonitorMLSesion,
    EstadoMonitorMlDTO,
    construir_fingerprint_estado_monitor_ml,
    derivar_estado_calidad_modelo,
    derivar_estado_monitor_ml,
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


def test_estado_monitor_ml_prioriza_alerta_y_recomendacion_fuerte() -> None:
    historial = [_historial(calidad="ROJO"), _historial(calidad="ROJO"), _historial(calidad="ROJO")]
    estado_calidad = derivar_estado_calidad_modelo(_resumen(accuracy=0.45, recall=0.35))

    estado_monitor = derivar_estado_monitor_ml(historial, estado_calidad=estado_calidad)

    assert estado_monitor.alerta_activa is True
    assert estado_monitor.recomendacion_operativa == "ACCION_REVISAR_DATOS"
    assert estado_monitor.recomendacion_fuerte is True
    assert (
        estado_monitor.recomendacion_razon_corta_i18n_key
        == "prediccion_ausencias.recomendacion_operativa.razon.rojos_consecutivos"
    )


def test_estado_monitor_ml_recomendacion_suave_si_empeora_sin_alerta() -> None:
    historial = [
        _historial(calidad="AMARILLO"),
        HistorialEntrenamientoModeloDTO(
            fecha_entrenamiento="2026-03-24T10:00:00+00:00",
            model_type="PredictorAusenciasBaseline",
            version="prediccion_ausencias_v1",
            citas_usadas=60,
            muestras_train=48,
            muestras_validacion=12,
            accuracy=0.64,
            precision_no_show=0.5,
            recall_no_show=0.51,
            f1_no_show=0.5,
            calidad_ux="VERDE",
            ganador_criterio="f1",
            baseline_f1=0.4,
            v2_f1=0.5,
        ),
    ]
    estado_calidad = derivar_estado_calidad_modelo(_resumen(accuracy=0.55, recall=0.45))

    estado_monitor = derivar_estado_monitor_ml(historial, estado_calidad=estado_calidad)

    assert estado_monitor.alerta_activa is False
    assert estado_monitor.estado_tendencia == "EMPEORA"
    assert estado_monitor.recomendacion_operativa == "ACCION_MONITORIZAR"
    assert (
        estado_monitor.recomendacion_razon_corta_i18n_key
        == "prediccion_ausencias.recomendacion_operativa.razon.tendencia_empeora"
    )


def test_estado_monitor_ml_sin_accion_si_no_hay_historial() -> None:
    estado_calidad = derivar_estado_calidad_modelo(_resumen(accuracy=0.7, recall=0.65))

    estado_monitor = derivar_estado_monitor_ml([], estado_calidad=estado_calidad)

    assert estado_monitor.estado_tendencia == "NO_DISPONIBLE"
    assert estado_monitor.recomendacion_operativa == "SIN_ACCION"
    assert (
        estado_monitor.recomendacion_razon_corta_i18n_key
        == "prediccion_ausencias.recomendacion_operativa.razon.sin_datos_suficientes"
    )


def _estado_monitor_base() -> EstadoMonitorMlDTO:
    return EstadoMonitorMlDTO(
        estado_tendencia="EMPEORA",
        alerta_activa=False,
        calidad_ultimo_entrenamiento="AMARILLO",
        recomendacion_operativa="ACCION_MONITORIZAR",
        recomendacion_i18n_key="prediccion_ausencias.recomendacion_operativa.accion_monitorizar",
        recomendacion_razon_corta_i18n_key="prediccion_ausencias.recomendacion_operativa.razon.tendencia_empeora",
        recomendacion_fuerte=False,
    )


def test_dedupe_telemetria_no_emite_si_fingerprint_no_cambia() -> None:
    dedupe = DedupeTelemetriaMonitorMLSesion()
    estado = _estado_monitor_base()

    assert dedupe.debe_emitir(estado) is True
    assert dedupe.debe_emitir(estado) is False


def test_dedupe_telemetria_emite_si_fingerprint_cambia() -> None:
    dedupe = DedupeTelemetriaMonitorMLSesion()
    estado = _estado_monitor_base()
    estado_actualizado = EstadoMonitorMlDTO(
        estado_tendencia="ESTABLE",
        alerta_activa=False,
        calidad_ultimo_entrenamiento="AMARILLO",
        recomendacion_operativa="SIN_ACCION",
        recomendacion_i18n_key="prediccion_ausencias.recomendacion_operativa.sin_accion",
        recomendacion_razon_corta_i18n_key=(
            "prediccion_ausencias.recomendacion_operativa.razon.sin_senales_preocupantes"
        ),
        recomendacion_fuerte=False,
    )

    assert dedupe.debe_emitir(estado) is True
    assert dedupe.debe_emitir(estado_actualizado) is True
    assert construir_fingerprint_estado_monitor_ml(estado) != construir_fingerprint_estado_monitor_ml(
        estado_actualizado
    )

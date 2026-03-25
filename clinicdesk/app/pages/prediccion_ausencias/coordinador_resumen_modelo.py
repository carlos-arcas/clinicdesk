from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    HistorialEntrenamientoModeloDTO,
    ResumenEntrenamientoModeloDTO,
    ResumenTendenciaHistorialDTO,
)
from clinicdesk.app.application.prediccion_ausencias.tendencia_entrenamientos import (
    calcular_resumen_tendencia_historial,
    derivar_recomendacion_operativa_monitor_ml,
)


@dataclass(frozen=True, slots=True)
class EstadoCalidadModeloDTO:
    estado: str
    i18n_key: str


@dataclass(frozen=True, slots=True)
class FilaHistorialEntrenamientoCompactoDTO:
    fecha_entrenamiento: str
    model_type: str
    accuracy: float | None
    recall_no_show: float | None
    calidad_ux: str


@dataclass(frozen=True, slots=True)
class EstadoTendenciaHistorialDTO:
    tendencia_accuracy_i18n_key: str
    tendencia_recall_i18n_key: str
    alerta_i18n_key: str
    alerta_activa: bool


@dataclass(frozen=True, slots=True)
class EstadoMonitorMlDTO:
    estado_tendencia: str
    alerta_activa: bool
    calidad_ultimo_entrenamiento: str
    recomendacion_operativa: str
    recomendacion_i18n_key: str
    recomendacion_fuerte: bool


def derivar_estado_calidad_modelo(resumen: ResumenEntrenamientoModeloDTO) -> EstadoCalidadModeloDTO:
    accuracy = resumen.accuracy or 0.0
    recall = resumen.recall_no_show or 0.0
    if accuracy >= 0.65 and recall >= 0.6:
        return EstadoCalidadModeloDTO("VERDE", "prediccion_ausencias.resumen_modelo.calidad.verde")
    if accuracy >= 0.5 and recall >= 0.4:
        return EstadoCalidadModeloDTO("AMARILLO", "prediccion_ausencias.resumen_modelo.calidad.amarillo")
    return EstadoCalidadModeloDTO("ROJO", "prediccion_ausencias.resumen_modelo.calidad.rojo")


def construir_filas_historial_compacto(
    historial: list[HistorialEntrenamientoModeloDTO], *, limite: int = 5
) -> list[FilaHistorialEntrenamientoCompactoDTO]:
    if limite <= 0:
        return []
    return [
        FilaHistorialEntrenamientoCompactoDTO(
            fecha_entrenamiento=item.fecha_entrenamiento,
            model_type=item.model_type,
            accuracy=item.accuracy,
            recall_no_show=item.recall_no_show,
            calidad_ux=item.calidad_ux,
        )
        for item in historial[:limite]
    ]


def derivar_estado_tendencia_historial(
    historial: list[HistorialEntrenamientoModeloDTO],
) -> EstadoTendenciaHistorialDTO:
    resumen = calcular_resumen_tendencia_historial(historial)
    return EstadoTendenciaHistorialDTO(
        tendencia_accuracy_i18n_key=_i18n_tendencia(resumen.tendencia_accuracy),
        tendencia_recall_i18n_key=_i18n_tendencia(resumen.tendencia_recall_no_show),
        alerta_i18n_key=_i18n_alerta(resumen),
        alerta_activa=resumen.alerta_rojo_consecutivo,
    )


def derivar_estado_monitor_ml(
    historial: list[HistorialEntrenamientoModeloDTO],
    *,
    estado_calidad: EstadoCalidadModeloDTO,
) -> EstadoMonitorMlDTO:
    resumen = calcular_resumen_tendencia_historial(historial)
    recomendacion = derivar_recomendacion_operativa_monitor_ml(
        resumen_tendencia=resumen,
        calidad_ultimo_entrenamiento=_calidad_ultimo_entrenamiento(historial, estado_calidad),
    )
    return EstadoMonitorMlDTO(
        estado_tendencia=_estado_tendencia_monitor(resumen),
        alerta_activa=resumen.alerta_rojo_consecutivo,
        calidad_ultimo_entrenamiento=_calidad_ultimo_entrenamiento(historial, estado_calidad),
        recomendacion_operativa=recomendacion.codigo,
        recomendacion_i18n_key=recomendacion.i18n_key,
        recomendacion_fuerte=recomendacion.es_fuerte,
    )


def _i18n_tendencia(tendencia: str) -> str:
    tendencia_normalizada = tendencia.lower()
    return f"prediccion_ausencias.historial.tendencia.valor.{tendencia_normalizada}"


def _i18n_alerta(resumen: ResumenTendenciaHistorialDTO) -> str:
    if resumen.alerta_rojo_consecutivo:
        return "prediccion_ausencias.historial.alerta.rojo_activa"
    if resumen.rojos_consecutivos > 0:
        return "prediccion_ausencias.historial.alerta.rojo_inactiva"
    return "prediccion_ausencias.historial.alerta.sin_rojos"


def _calidad_ultimo_entrenamiento(
    historial: list[HistorialEntrenamientoModeloDTO], estado_calidad: EstadoCalidadModeloDTO
) -> str:
    if not historial:
        return estado_calidad.estado
    return historial[0].calidad_ux


def _estado_tendencia_monitor(resumen: ResumenTendenciaHistorialDTO) -> str:
    valores = (resumen.tendencia_accuracy, resumen.tendencia_recall_no_show)
    if "EMPEORA" in valores:
        return "EMPEORA"
    if "MEJORA" in valores:
        return "MEJORA"
    if all(valor == "NO_DISPONIBLE" for valor in valores):
        return "NO_DISPONIBLE"
    return "ESTABLE"

from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    HistorialEntrenamientoModeloDTO,
    ResumenEntrenamientoModeloDTO,
    ResumenTendenciaHistorialDTO,
)
from clinicdesk.app.application.prediccion_ausencias.tendencia_entrenamientos import (
    calcular_resumen_tendencia_historial,
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


def _i18n_tendencia(tendencia: str) -> str:
    tendencia_normalizada = tendencia.lower()
    return f"prediccion_ausencias.historial.tendencia.valor.{tendencia_normalizada}"


def _i18n_alerta(resumen: ResumenTendenciaHistorialDTO) -> str:
    if resumen.alerta_rojo_consecutivo:
        return "prediccion_ausencias.historial.alerta.rojo_activa"
    if resumen.rojos_consecutivos > 0:
        return "prediccion_ausencias.historial.alerta.rojo_inactiva"
    return "prediccion_ausencias.historial.alerta.sin_rojos"

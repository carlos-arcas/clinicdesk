from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    HistorialEntrenamientoModeloDTO,
    ResumenEntrenamientoModeloDTO,
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

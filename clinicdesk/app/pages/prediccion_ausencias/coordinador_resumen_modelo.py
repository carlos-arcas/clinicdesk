from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.dtos import ResumenEntrenamientoModeloDTO


@dataclass(frozen=True, slots=True)
class EstadoCalidadModeloDTO:
    estado: str
    i18n_key: str


def derivar_estado_calidad_modelo(resumen: ResumenEntrenamientoModeloDTO) -> EstadoCalidadModeloDTO:
    accuracy = resumen.accuracy or 0.0
    recall = resumen.recall_no_show or 0.0
    if accuracy >= 0.65 and recall >= 0.6:
        return EstadoCalidadModeloDTO("VERDE", "prediccion_ausencias.resumen_modelo.calidad.verde")
    if accuracy >= 0.5 and recall >= 0.4:
        return EstadoCalidadModeloDTO("AMARILLO", "prediccion_ausencias.resumen_modelo.calidad.amarillo")
    return EstadoCalidadModeloDTO("ROJO", "prediccion_ausencias.resumen_modelo.calidad.rojo")

from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    HistorialEntrenamientoModeloDTO,
    ResumenTendenciaHistorialDTO,
)

TENDENCIA_MEJORA = "MEJORA"
TENDENCIA_EMPEORA = "EMPEORA"
TENDENCIA_ESTABLE = "ESTABLE"
TENDENCIA_NO_DISPONIBLE = "NO_DISPONIBLE"
_TOLERANCIA_DELTA = 0.005
_CALIDAD_ROJO = "ROJO"


def calcular_resumen_tendencia_historial(
    historial: list[HistorialEntrenamientoModeloDTO], *, umbral_alerta_rojo: int = 3
) -> ResumenTendenciaHistorialDTO:
    if len(historial) < 2:
        return ResumenTendenciaHistorialDTO(
            tendencia_accuracy=TENDENCIA_NO_DISPONIBLE,
            tendencia_recall_no_show=TENDENCIA_NO_DISPONIBLE,
            alerta_rojo_consecutivo=False,
            rojos_consecutivos=_contar_rojos_consecutivos(historial),
        )
    ultimo, anterior = historial[0], historial[1]
    rojos_consecutivos = _contar_rojos_consecutivos(historial)
    return ResumenTendenciaHistorialDTO(
        tendencia_accuracy=_derivar_tendencia(ultimo.accuracy, anterior.accuracy),
        tendencia_recall_no_show=_derivar_tendencia(ultimo.recall_no_show, anterior.recall_no_show),
        alerta_rojo_consecutivo=rojos_consecutivos >= umbral_alerta_rojo,
        rojos_consecutivos=rojos_consecutivos,
    )


def _derivar_tendencia(valor_actual: float | None, valor_anterior: float | None) -> str:
    if valor_actual is None or valor_anterior is None:
        return TENDENCIA_NO_DISPONIBLE
    delta = valor_actual - valor_anterior
    if delta > _TOLERANCIA_DELTA:
        return TENDENCIA_MEJORA
    if delta < -_TOLERANCIA_DELTA:
        return TENDENCIA_EMPEORA
    return TENDENCIA_ESTABLE


def _contar_rojos_consecutivos(historial: list[HistorialEntrenamientoModeloDTO]) -> int:
    consecutivos = 0
    for item in historial:
        if item.calidad_ux != _CALIDAD_ROJO:
            break
        consecutivos += 1
    return consecutivos

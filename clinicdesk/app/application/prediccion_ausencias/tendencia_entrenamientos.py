from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.dtos import (
    HistorialEntrenamientoModeloDTO,
    RecomendacionOperativaMonitorMLDTO,
    ResumenTendenciaHistorialDTO,
)

TENDENCIA_MEJORA = "MEJORA"
TENDENCIA_EMPEORA = "EMPEORA"
TENDENCIA_ESTABLE = "ESTABLE"
TENDENCIA_NO_DISPONIBLE = "NO_DISPONIBLE"
_TOLERANCIA_DELTA = 0.005
_CALIDAD_ROJO = "ROJO"
ACCION_REENTRENAR = "ACCION_REENTRENAR"
ACCION_REVISAR_DATOS = "ACCION_REVISAR_DATOS"
ACCION_MONITORIZAR = "ACCION_MONITORIZAR"
SIN_ACCION = "SIN_ACCION"


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


def derivar_recomendacion_operativa_monitor_ml(
    *,
    resumen_tendencia: ResumenTendenciaHistorialDTO,
    calidad_ultimo_entrenamiento: str | None,
) -> RecomendacionOperativaMonitorMLDTO:
    calidad_normalizada = (calidad_ultimo_entrenamiento or "").upper()
    if resumen_tendencia.alerta_rojo_consecutivo:
        if calidad_normalizada == _CALIDAD_ROJO:
            return RecomendacionOperativaMonitorMLDTO(
                codigo=ACCION_REVISAR_DATOS,
                i18n_key="prediccion_ausencias.recomendacion_operativa.accion_revisar_datos",
                es_fuerte=True,
            )
        return RecomendacionOperativaMonitorMLDTO(
            codigo=ACCION_REENTRENAR,
            i18n_key="prediccion_ausencias.recomendacion_operativa.accion_reentrenar",
            es_fuerte=True,
        )
    if _tendencia_empeora(resumen_tendencia):
        return RecomendacionOperativaMonitorMLDTO(
            codigo=ACCION_MONITORIZAR,
            i18n_key="prediccion_ausencias.recomendacion_operativa.accion_monitorizar",
            es_fuerte=False,
        )
    return RecomendacionOperativaMonitorMLDTO(
        codigo=SIN_ACCION,
        i18n_key="prediccion_ausencias.recomendacion_operativa.sin_accion",
        es_fuerte=False,
    )


def _tendencia_empeora(resumen_tendencia: ResumenTendenciaHistorialDTO) -> bool:
    return (
        resumen_tendencia.tendencia_accuracy == TENDENCIA_EMPEORA
        or resumen_tendencia.tendencia_recall_no_show == TENDENCIA_EMPEORA
    )

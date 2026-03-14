from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from clinicdesk.app.application.ml.drift_explain import explain_drift


class SemaforoLecturaML(str, Enum):
    VERDE = "verde"
    AMARILLO = "amarillo"
    ROJO = "rojo"


@dataclass(frozen=True, slots=True)
class TextoI18n:
    clave: str
    params: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AccionOperativaSugerida:
    clave_accion: str
    descripcion: TextoI18n
    urgencia: str


@dataclass(frozen=True, slots=True)
class RiesgoLecturaML:
    descripcion: TextoI18n
    impacto: str


@dataclass(frozen=True, slots=True)
class UtilidadLecturaML:
    descripcion: TextoI18n
    decision_habilitada: TextoI18n


@dataclass(frozen=True, slots=True)
class LecturaOperativaML:
    lectura_origen: str
    resumen_humano: TextoI18n
    utilidad: UtilidadLecturaML
    nivel_confianza: str
    semaforo: SemaforoLecturaML
    riesgo_principal: RiesgoLecturaML
    accion_sugerida: AccionOperativaSugerida
    cuando_mirar: TextoI18n
    cuando_no_concluir_fuerte: TextoI18n
    que_no_significa: TextoI18n


def construir_lectura_operativa_scoring(total: int, riesgo_alto: int) -> LecturaOperativaML:
    if total <= 0:
        return LecturaOperativaML(
            lectura_origen="scoring",
            resumen_humano=TextoI18n("demo_ml.operativa.score.sin_datos"),
            utilidad=UtilidadLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.score.sin_datos.utilidad"),
                decision_habilitada=TextoI18n("demo_ml.operativa.score.sin_datos.decision"),
            ),
            nivel_confianza="baja",
            semaforo=SemaforoLecturaML.ROJO,
            riesgo_principal=RiesgoLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.score.sin_datos.riesgo"),
                impacto="alto",
            ),
            accion_sugerida=AccionOperativaSugerida(
                clave_accion="preparar_dataset",
                descripcion=TextoI18n("demo_ml.operativa.score.sin_datos.accion"),
                urgencia="alta",
            ),
            cuando_mirar=TextoI18n("demo_ml.operativa.score.sin_datos.cuando_mirar"),
            cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.score.sin_datos.no_concluir"),
            que_no_significa=TextoI18n("demo_ml.operativa.score.sin_datos.no_significa"),
        )

    porcentaje = (riesgo_alto / total) * 100
    semaforo = SemaforoLecturaML.VERDE
    confianza = "media"
    if total < 20:
        semaforo = SemaforoLecturaML.AMARILLO
        confianza = "baja"
    elif porcentaje >= 60:
        semaforo = SemaforoLecturaML.AMARILLO

    return LecturaOperativaML(
        lectura_origen="scoring",
        resumen_humano=TextoI18n(
            "demo_ml.operativa.score.resumen",
            {"riesgo_alto": riesgo_alto, "total": total, "porcentaje": f"{porcentaje:.1f}"},
        ),
        utilidad=UtilidadLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.score.utilidad"),
            decision_habilitada=TextoI18n("demo_ml.operativa.score.decision"),
        ),
        nivel_confianza=confianza,
        semaforo=semaforo,
        riesgo_principal=RiesgoLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.score.riesgo"),
            impacto="medio",
        ),
        accion_sugerida=AccionOperativaSugerida(
            clave_accion="priorizar_recordatorios",
            descripcion=TextoI18n("demo_ml.operativa.score.accion"),
            urgencia="media",
        ),
        cuando_mirar=TextoI18n("demo_ml.operativa.score.cuando_mirar"),
        cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.score.no_concluir"),
        que_no_significa=TextoI18n("demo_ml.operativa.score.no_significa"),
    )


def construir_lectura_operativa_drift(report: object | None) -> LecturaOperativaML:
    if report is None:
        return LecturaOperativaML(
            lectura_origen="drift",
            resumen_humano=TextoI18n("demo_ml.operativa.drift.sin_datos"),
            utilidad=UtilidadLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.drift.sin_datos.utilidad"),
                decision_habilitada=TextoI18n("demo_ml.operativa.drift.sin_datos.decision"),
            ),
            nivel_confianza="baja",
            semaforo=SemaforoLecturaML.AMARILLO,
            riesgo_principal=RiesgoLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.drift.sin_datos.riesgo"),
                impacto="medio",
            ),
            accion_sugerida=AccionOperativaSugerida(
                clave_accion="ejecutar_drift",
                descripcion=TextoI18n("demo_ml.operativa.drift.sin_datos.accion"),
                urgencia="media",
            ),
            cuando_mirar=TextoI18n("demo_ml.operativa.drift.sin_datos.cuando_mirar"),
            cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.drift.sin_datos.no_concluir"),
            que_no_significa=TextoI18n("demo_ml.operativa.drift.sin_datos.no_significa"),
        )

    severidad, _, psi_max = explain_drift(report)
    semaforo = {
        "GREEN": SemaforoLecturaML.VERDE,
        "AMBER": SemaforoLecturaML.AMARILLO,
        "RED": SemaforoLecturaML.ROJO,
    }[severidad.value]
    confianza = "alta" if semaforo != SemaforoLecturaML.ROJO else "media"
    accion_key = "demo_ml.operativa.drift.accion.revisar"
    if semaforo == SemaforoLecturaML.ROJO:
        accion_key = "demo_ml.operativa.drift.accion.investigar"

    return LecturaOperativaML(
        lectura_origen="drift",
        resumen_humano=TextoI18n(
            "demo_ml.operativa.drift.resumen",
            {"psi_max": f"{psi_max:.3f}", "severidad": severidad.value},
        ),
        utilidad=UtilidadLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.drift.utilidad"),
            decision_habilitada=TextoI18n("demo_ml.operativa.drift.decision"),
        ),
        nivel_confianza=confianza,
        semaforo=semaforo,
        riesgo_principal=RiesgoLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.drift.riesgo"),
            impacto="alto" if semaforo == SemaforoLecturaML.ROJO else "medio",
        ),
        accion_sugerida=AccionOperativaSugerida(
            clave_accion="revisar_estabilidad_dataset",
            descripcion=TextoI18n(accion_key),
            urgencia="alta" if semaforo == SemaforoLecturaML.ROJO else "media",
        ),
        cuando_mirar=TextoI18n("demo_ml.operativa.drift.cuando_mirar"),
        cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.drift.no_concluir"),
        que_no_significa=TextoI18n("demo_ml.operativa.drift.no_significa"),
    )


def construir_lectura_operativa_metricas(
    accuracy: float,
    precision: float,
    recall: float,
    test_row_count: int | None = None,
) -> LecturaOperativaML:
    minimo = min(accuracy, precision, recall)
    semaforo = SemaforoLecturaML.VERDE
    confianza = "media"
    if minimo < 0.55:
        semaforo = SemaforoLecturaML.ROJO
    elif minimo < 0.70:
        semaforo = SemaforoLecturaML.AMARILLO
    if (test_row_count or 0) and (test_row_count or 0) < 30:
        semaforo = SemaforoLecturaML.AMARILLO
        confianza = "baja"

    return LecturaOperativaML(
        lectura_origen="metricas_evaluacion",
        resumen_humano=TextoI18n(
            "demo_ml.operativa.metricas.resumen",
            {
                "accuracy": f"{accuracy:.2f}",
                "precision": f"{precision:.2f}",
                "recall": f"{recall:.2f}",
            },
        ),
        utilidad=UtilidadLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.metricas.utilidad"),
            decision_habilitada=TextoI18n("demo_ml.operativa.metricas.decision"),
        ),
        nivel_confianza=confianza,
        semaforo=semaforo,
        riesgo_principal=RiesgoLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.metricas.riesgo"),
            impacto="alto" if semaforo == SemaforoLecturaML.ROJO else "medio",
        ),
        accion_sugerida=AccionOperativaSugerida(
            clave_accion="validar_calidad_modelo",
            descripcion=TextoI18n("demo_ml.operativa.metricas.accion"),
            urgencia="alta" if semaforo == SemaforoLecturaML.ROJO else "media",
        ),
        cuando_mirar=TextoI18n("demo_ml.operativa.metricas.cuando_mirar"),
        cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.metricas.no_concluir"),
        que_no_significa=TextoI18n("demo_ml.operativa.metricas.no_significa"),
    )


def construir_lectura_operativa_exportacion(export_count: int) -> LecturaOperativaML:
    if export_count <= 0:
        return LecturaOperativaML(
            lectura_origen="exportacion",
            resumen_humano=TextoI18n("demo_ml.operativa.export.sin_archivos"),
            utilidad=UtilidadLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.export.sin_archivos.utilidad"),
                decision_habilitada=TextoI18n("demo_ml.operativa.export.sin_archivos.decision"),
            ),
            nivel_confianza="baja",
            semaforo=SemaforoLecturaML.ROJO,
            riesgo_principal=RiesgoLecturaML(
                descripcion=TextoI18n("demo_ml.operativa.export.sin_archivos.riesgo"),
                impacto="medio",
            ),
            accion_sugerida=AccionOperativaSugerida(
                clave_accion="exportar_corrida",
                descripcion=TextoI18n("demo_ml.operativa.export.sin_archivos.accion"),
                urgencia="media",
            ),
            cuando_mirar=TextoI18n("demo_ml.operativa.export.sin_archivos.cuando_mirar"),
            cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.export.sin_archivos.no_concluir"),
            que_no_significa=TextoI18n("demo_ml.operativa.export.sin_archivos.no_significa"),
        )

    return LecturaOperativaML(
        lectura_origen="exportacion",
        resumen_humano=TextoI18n("demo_ml.operativa.export.resumen", {"cantidad": export_count}),
        utilidad=UtilidadLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.export.utilidad"),
            decision_habilitada=TextoI18n("demo_ml.operativa.export.decision"),
        ),
        nivel_confianza="alta",
        semaforo=SemaforoLecturaML.VERDE,
        riesgo_principal=RiesgoLecturaML(
            descripcion=TextoI18n("demo_ml.operativa.export.riesgo"),
            impacto="bajo",
        ),
        accion_sugerida=AccionOperativaSugerida(
            clave_accion="compartir_bi",
            descripcion=TextoI18n("demo_ml.operativa.export.accion"),
            urgencia="media",
        ),
        cuando_mirar=TextoI18n("demo_ml.operativa.export.cuando_mirar"),
        cuando_no_concluir_fuerte=TextoI18n("demo_ml.operativa.export.no_concluir"),
        que_no_significa=TextoI18n("demo_ml.operativa.export.no_significa"),
    )

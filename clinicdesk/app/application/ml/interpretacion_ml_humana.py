from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ml.drift_explain import explain_drift


@dataclass(frozen=True, slots=True)
class InterpretacionHumana:
    titulo: str
    significado: str
    recomendacion: str


def interpretar_scoring(total: int, riesgo_alto: int) -> InterpretacionHumana:
    if total <= 0:
        return InterpretacionHumana(
            titulo="Scoring sin citas",
            significado="No hay citas para analizar, por lo que no se puede priorizar riesgo.",
            recomendacion="Genera o selecciona un dataset con citas y vuelve a puntuar.",
        )
    porcentaje = (riesgo_alto / total) * 100
    severidad = "alto" if porcentaje >= 30 else "medio" if porcentaje >= 15 else "bajo"
    return InterpretacionHumana(
        titulo=f"Scoring operativo ({severidad})",
        significado=f"{riesgo_alto} de {total} citas están marcadas con riesgo alto ({porcentaje:.1f}%).",
        recomendacion="Usa este dato para priorizar recordatorios y confirmaciones sobre las citas de mayor riesgo.",
    )


def interpretar_drift(report: object | None) -> InterpretacionHumana:
    if report is None:
        return InterpretacionHumana(
            titulo="Drift no disponible",
            significado="Aún no hay una comparación entre datasets.",
            recomendacion="Genera dos versiones de dataset y ejecuta drift para detectar cambios.",
        )
    severidad, mensaje, psi_max = explain_drift(report)
    return InterpretacionHumana(
        titulo=f"Drift {severidad.value}",
        significado=f"PSI máximo: {psi_max:.3f}. {mensaje}",
        recomendacion="Si el drift es AMBER o RED, revisa datos recientes y considera reentrenar antes de decidir.",
    )


def interpretar_entrenamiento(accuracy: float, precision: float, recall: float) -> InterpretacionHumana:
    return InterpretacionHumana(
        titulo="Resumen del entrenamiento",
        significado=(
            f"Accuracy {accuracy:.2f}, precision {precision:.2f}, recall {recall:.2f}. "
            "Estas métricas reflejan desempeño histórico y no garantizan resultados futuros."
        ),
        recomendacion="Compáralas con objetivos del negocio y valida con casos reales antes de automatizar decisiones.",
    )

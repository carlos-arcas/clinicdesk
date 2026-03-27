from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ml.drift_explain import explain_drift


@dataclass(frozen=True, slots=True)
class InterpretacionHumana:
    titulo: str
    significado: str
    recomendacion: str
    utilidad_practica: str
    cuando_revisar: str
    decision_que_habilita: str
    limite: str


def interpretar_scoring(total: int, riesgo_alto: int) -> InterpretacionHumana:
    if total <= 0:
        return InterpretacionHumana(
            titulo="Scoring sin citas",
            significado="No hay citas para analizar, por lo que no se puede priorizar riesgo.",
            recomendacion="Genera o selecciona un dataset con citas y vuelve a puntuar.",
            utilidad_practica="Evita tomar decisiones operativas basadas en muestras vacías.",
            cuando_revisar="Revísalo justo después de preparar un dataset con citas válidas.",
            decision_que_habilita="Decidir si se puede iniciar la priorización operativa.",
            limite="Sin volumen mínimo de citas no hay señal fiable para priorizar.",
        )
    porcentaje = (riesgo_alto / total) * 100
    severidad = "alto" if porcentaje >= 30 else "medio" if porcentaje >= 15 else "bajo"
    return InterpretacionHumana(
        titulo=f"Scoring operativo ({severidad})",
        significado=f"{riesgo_alto} de {total} citas están marcadas con riesgo alto ({porcentaje:.1f}%).",
        recomendacion="Usa este dato para priorizar recordatorios y confirmaciones sobre las citas de mayor riesgo.",
        utilidad_practica="Permite enfocar recursos en las citas con mayor probabilidad de inasistencia.",
        cuando_revisar="Cada vez que se complete un nuevo scoring de la agenda activa.",
        decision_que_habilita="Definir el orden de seguimiento y contacto proactivo.",
        limite="Es una señal probabilística y no sustituye validaciones clínicas u operativas.",
    )


def interpretar_drift(report: object | None) -> InterpretacionHumana:
    if report is None:
        return InterpretacionHumana(
            titulo="Drift no disponible",
            significado="Aún no hay una comparación entre datasets.",
            recomendacion="Genera dos versiones de dataset y ejecuta drift para detectar cambios.",
            utilidad_practica="Evita asumir estabilidad cuando aún no existe evidencia comparativa.",
            cuando_revisar="Tras generar una nueva versión de dataset sobre un periodo distinto.",
            decision_que_habilita="Decidir si conviene habilitar monitorización de cambios.",
            limite="Sin baseline comparativo no se puede concluir si hubo cambio de patrón.",
        )
    severidad, mensaje, psi_max = explain_drift(report)
    return InterpretacionHumana(
        titulo=f"Drift {severidad.value}",
        significado=f"PSI máximo: {psi_max:.3f}. {mensaje}",
        recomendacion="Si el drift es AMBER o RED, revisa datos recientes y considera reentrenar antes de decidir.",
        utilidad_practica="Ayuda a detectar pérdida de vigencia del modelo por cambios en el comportamiento.",
        cuando_revisar="Cuando cambie la ventana temporal de datos o antes de campañas críticas.",
        decision_que_habilita="Decidir si mantener modelo actual o reentrenar.",
        limite="No explica por sí solo el impacto clínico, solo alerta sobre cambio estadístico.",
    )


def interpretar_entrenamiento(accuracy: float, precision: float, recall: float) -> InterpretacionHumana:
    return InterpretacionHumana(
        titulo="Resumen del entrenamiento",
        significado=(
            f"Accuracy {accuracy:.2f}, precision {precision:.2f}, recall {recall:.2f}. "
            "Estas métricas reflejan desempeño histórico y no garantizan resultados futuros."
        ),
        recomendacion="Compáralas con objetivos del negocio y valida con casos reales antes de automatizar decisiones.",
        utilidad_practica="Sirve para decidir si el modelo alcanza la calidad mínima esperada.",
        cuando_revisar="Después de cada entrenamiento o recalibración de umbral.",
        decision_que_habilita="Aprobar uso operativo, ajustar umbral o pedir nuevo entrenamiento.",
        limite="Métricas offline no sustituyen validación continua en operación real.",
    )


def interpretar_evaluacion(accuracy: float, precision: float, recall: float) -> InterpretacionHumana:
    return InterpretacionHumana(
        titulo="Resumen de evaluación",
        significado=(f"Evaluación offline: accuracy {accuracy:.2f}, precision {precision:.2f}, recall {recall:.2f}."),
        recomendacion="Si no cumple umbral operativo, mejora datos o recalibra antes de desplegar decisiones automáticas.",
        utilidad_practica="Sirve para aprobar o frenar el paso a uso operativo.",
        cuando_revisar="Después de entrenar, antes de activar scoring recurrente.",
        decision_que_habilita="Autorizar piloto, recalibrar o reentrenar.",
        limite="Una sola evaluación no representa toda la variabilidad futura.",
    )


def interpretar_exportacion(export_count: int) -> InterpretacionHumana:
    if export_count <= 0:
        return InterpretacionHumana(
            titulo="Exportación pendiente",
            significado="No hay archivos exportados en esta ejecución.",
            recomendacion="Exporta artefactos para compartir resultados y trazabilidad con operaciones.",
            utilidad_practica="Habilita consumo en BI, auditoría y seguimiento externo.",
            cuando_revisar="Al cerrar cada corrida de análisis relevante.",
            decision_que_habilita="Decidir si el resultado está listo para distribución.",
            limite="Sin export, los hallazgos quedan aislados en la sesión local.",
        )
    return InterpretacionHumana(
        titulo="Exportación disponible",
        significado=f"Se detectaron {export_count} artefactos exportados para consumo externo.",
        recomendacion="Comparte los CSV con operación y usa la misma corrida como referencia de seguimiento.",
        utilidad_practica="Facilita decisiones coordinadas entre perfiles no técnicos.",
        cuando_revisar="Cuando se publique una nueva versión de scoring o drift.",
        decision_que_habilita="Validar cierre de ciclo y comunicación de resultados.",
        limite="Exportar no valida calidad del modelo, solo disponibilidad de artefactos.",
    )

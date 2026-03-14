from __future__ import annotations

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.interpretacion_ml_humana import (
    interpretar_drift,
    interpretar_entrenamiento,
    interpretar_evaluacion,
    interpretar_exportacion,
    interpretar_scoring,
)


def test_interpretar_scoring_devuelve_recomendacion_operativa() -> None:
    salida = interpretar_scoring(total=20, riesgo_alto=8)
    assert "40.0%" in salida.significado
    assert "priorizar" in salida.recomendacion.lower()
    assert "foco" in salida.utilidad_practica.lower() or "enfocar" in salida.utilidad_practica.lower()


def test_interpretar_drift_sin_reporte() -> None:
    salida = interpretar_drift(None)
    assert salida.titulo == "Drift no disponible"
    assert "baseline" in salida.limite.lower() or "comparativo" in salida.limite.lower()


def test_interpretar_entrenamiento_aclara_limites() -> None:
    salida = interpretar_entrenamiento(0.82, 0.7, 0.65)
    assert "no garantizan" in salida.significado
    assert "offline" not in salida.recomendacion.lower()


def test_interpretar_drift_con_reporte() -> None:
    report = DriftReport(
        from_version="v1",
        to_version="v2",
        total_from=10,
        total_to=10,
        feature_shifts={"duracion_bucket": {"30-45": 0.0}},
        psi_by_feature={"duracion_bucket": 0.01},
        overall_flag=False,
    )
    salida = interpretar_drift(report)
    assert "PSI máximo" in salida.significado
    assert "reentrenar" in salida.recomendacion.lower()


def test_interpretar_evaluacion_orienta_decision() -> None:
    salida = interpretar_evaluacion(0.81, 0.7, 0.66)
    assert "evaluación offline" in salida.significado.lower()
    assert "aprobar" in salida.utilidad_practica.lower() or "frenar" in salida.utilidad_practica.lower()


def test_interpretar_exportacion_indica_si_hay_artefactos() -> None:
    pendiente = interpretar_exportacion(0)
    disponible = interpretar_exportacion(4)
    assert "pendiente" in pendiente.titulo.lower()
    assert "4" in disponible.significado

from __future__ import annotations

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.interpretacion_ml_humana import (
    interpretar_drift,
    interpretar_entrenamiento,
    interpretar_scoring,
)


def test_interpretar_scoring_devuelve_recomendacion_operativa() -> None:
    salida = interpretar_scoring(total=20, riesgo_alto=8)
    assert "40.0%" in salida.significado
    assert "priorizar" in salida.recomendacion.lower()


def test_interpretar_drift_sin_reporte() -> None:
    salida = interpretar_drift(None)
    assert salida.titulo == "Drift no disponible"


def test_interpretar_entrenamiento_aclara_limites() -> None:
    salida = interpretar_entrenamiento(0.82, 0.7, 0.65)
    assert "no garantizan" in salida.significado


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

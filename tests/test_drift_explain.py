from __future__ import annotations

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.drift_explain import DriftSeverity, explain_drift


def _report(psi_value: float) -> DriftReport:
    return DriftReport(
        from_version="v1",
        to_version="v2",
        total_from=10,
        total_to=10,
        feature_shifts={},
        psi_by_feature={"duracion_bucket": psi_value},
        overall_flag=psi_value >= 0.2,
    )


def test_explain_drift_returns_green_message_for_low_psi() -> None:
    severity, message, psi_max = explain_drift(_report(0.05))

    assert severity is DriftSeverity.GREEN
    assert "Sin cambios relevantes" in message
    assert psi_max == 0.05


def test_explain_drift_returns_amber_message_for_medium_psi() -> None:
    severity, message, _ = explain_drift(_report(0.15))

    assert severity is DriftSeverity.AMBER
    assert "Cambios moderados" in message


def test_explain_drift_returns_red_message_for_high_psi() -> None:
    severity, message, _ = explain_drift(_report(0.21))

    assert severity is DriftSeverity.RED
    assert "reentrenamiento" in message

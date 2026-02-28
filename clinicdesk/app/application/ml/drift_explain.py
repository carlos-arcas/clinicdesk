from __future__ import annotations

from enum import Enum

from clinicdesk.app.application.ml.drift import DriftReport


class DriftSeverity(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


def severity_from_psi(psi_value: float) -> DriftSeverity:
    if psi_value < 0.1:
        return DriftSeverity.GREEN
    if psi_value < 0.2:
        return DriftSeverity.AMBER
    return DriftSeverity.RED


def explain_drift(report: DriftReport) -> tuple[DriftSeverity, str, float]:
    psi_max = _max_psi(report)
    severity = severity_from_psi(psi_max)
    message = _message_for_severity(severity)
    return severity, message, psi_max


def _max_psi(report: DriftReport) -> float:
    if not report.psi_by_feature:
        return 0.0
    return max(float(value) for value in report.psi_by_feature.values())


def _message_for_severity(severity: DriftSeverity) -> str:
    if severity is DriftSeverity.GREEN:
        return "Sin cambios relevantes detectados."
    if severity is DriftSeverity.AMBER:
        return "Cambios moderados: conviene revisar."
    return "Cambios significativos: el modelo podría necesitar reentrenamiento."

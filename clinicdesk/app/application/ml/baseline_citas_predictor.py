from __future__ import annotations

from clinicdesk.app.application.ports.predictor_port import (
    PredictionResult,
    PredictorInput,
    PredictorPort,
)


class BaselineCitasPredictor(PredictorPort):
    """Predictor determinista de baseline para priorización inicial de riesgo."""

    def predict_one(self, x: PredictorInput) -> PredictionResult:
        score, reasons = _compute_score_and_reasons(x)
        return PredictionResult(score=score, label=_to_label(score), reasons=reasons)

    def predict_batch(self, xs: list[PredictorInput]) -> list[PredictionResult]:
        return [self.predict_one(x) for x in xs]


def _compute_score_and_reasons(x: PredictorInput) -> tuple[float, list[str]]:
    score = 0.05
    reasons: list[str] = []

    score = _add_boolean_signal(score, x.has_incidencias, 0.35, "has_incidencias", reasons)
    score = _add_boolean_signal(score, x.is_suspicious, 0.30, "is_suspicious", reasons)
    score = _add_bucket_signal(score, x.duracion_bucket, _duracion_weights(), "duracion", reasons)
    score = _add_boolean_signal(score, x.is_weekend, 0.07, "is_weekend", reasons)
    score = _add_bucket_signal(score, x.notas_len_bucket, _notas_weights(), "notas", reasons)

    if x.estado_norm == "no_show":
        score += 0.20
        reasons.append("estado_no_show")

    if not reasons:
        reasons.append("baseline_low_signal")
    return _clamp_01(score), reasons


def _duracion_weights() -> dict[str, float]:
    return {"0-10": 0.00, "11-20": 0.08, "21-40": 0.16, "41+": 0.24}


def _notas_weights() -> dict[str, float]:
    return {"0": 0.00, "1-20": 0.03, "21-100": 0.08, "101+": 0.13}


def _add_boolean_signal(
    score: float,
    is_enabled: bool,
    weight: float,
    reason: str,
    reasons: list[str],
) -> float:
    if not is_enabled:
        return score
    reasons.append(reason)
    return score + weight


def _add_bucket_signal(
    score: float,
    bucket: str,
    weights: dict[str, float],
    reason_prefix: str,
    reasons: list[str],
) -> float:
    weight = weights.get(bucket, 0.0)
    if weight > 0:
        reasons.append(f"{reason_prefix}_bucket={bucket}")
    return score + weight


def _to_label(score: float) -> str:
    if score < 0.34:
        return "low"
    if score < 0.67:
        return "medium"
    return "high"


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, value))

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.targets import derive_target_from_feature
from clinicdesk.app.application.ports.predictor_port import PredictionResult

_ALPHA = 1.0


@dataclass(slots=True)
class TrainedModel:
    model_name: str
    class_counts: dict[str, int]
    feature_counts: dict[str, dict[str, dict[str, int]]]
    feature_value_cardinality: dict[str, int]
    alpha: float = _ALPHA


def train(rows: list[CitasFeatureRow]) -> TrainedModel:
    class_counts = {"0": 0, "1": 0}
    feature_counts = _empty_feature_counts()

    for row in rows:
        target = str(derive_target_from_feature(row))
        class_counts[target] += 1
        for name, value in _feature_tokens(row).items():
            per_class = feature_counts[name].setdefault(target, {})
            per_class[value] = per_class.get(value, 0) + 1

    return TrainedModel(
        model_name="citas_nb_v1",
        class_counts=class_counts,
        feature_counts=feature_counts,
        feature_value_cardinality=_feature_value_cardinality(feature_counts),
    )


def predict_one(model: TrainedModel, row: CitasFeatureRow) -> PredictionResult:
    score = _posterior_positive_probability(model, row)
    return PredictionResult(score=score, label=_to_label(score), reasons=["predictor=naive_bayes"])


def predict_batch(model: TrainedModel, rows: list[CitasFeatureRow]) -> list[PredictionResult]:
    return [predict_one(model, row) for row in rows]


def model_to_dict(model: TrainedModel) -> dict[str, Any]:
    return {
        "model_name": model.model_name,
        "class_counts": model.class_counts,
        "feature_counts": model.feature_counts,
        "feature_value_cardinality": model.feature_value_cardinality,
        "alpha": model.alpha,
    }


def model_from_dict(payload: dict[str, Any]) -> TrainedModel:
    return TrainedModel(
        model_name=str(payload["model_name"]),
        class_counts={k: int(v) for k, v in dict(payload["class_counts"]).items()},
        feature_counts={
            feature: {
                klass: {token: int(count) for token, count in dict(counts).items()}
                for klass, counts in dict(per_class).items()
            }
            for feature, per_class in dict(payload["feature_counts"]).items()
        },
        feature_value_cardinality={
            feature: int(cardinality)
            for feature, cardinality in dict(payload["feature_value_cardinality"]).items()
        },
        alpha=float(payload.get("alpha", _ALPHA)),
    )


def _posterior_positive_probability(model: TrainedModel, row: CitasFeatureRow) -> float:
    total = model.class_counts["0"] + model.class_counts["1"]
    if total == 0:
        return 0.5

    log_prob_0 = math.log(_smoothed_prior(model.class_counts["0"], total, 2, model.alpha))
    log_prob_1 = math.log(_smoothed_prior(model.class_counts["1"], total, 2, model.alpha))

    for name, token in _feature_tokens(row).items():
        log_prob_0 += math.log(_smoothed_likelihood(model, name, token, "0"))
        log_prob_1 += math.log(_smoothed_likelihood(model, name, token, "1"))

    prob_1 = _sigmoid_from_log_odds(log_prob_1 - log_prob_0)
    return max(0.0, min(1.0, prob_1))


def _smoothed_prior(class_count: int, total: int, num_classes: int, alpha: float) -> float:
    return (class_count + alpha) / (total + alpha * num_classes)


def _smoothed_likelihood(model: TrainedModel, feature: str, token: str, klass: str) -> float:
    per_class = model.feature_counts.get(feature, {}).get(klass, {})
    token_count = per_class.get(token, 0)
    feature_total = sum(per_class.values())
    cardinality = max(model.feature_value_cardinality.get(feature, 1), 1)
    return (token_count + model.alpha) / (feature_total + model.alpha * cardinality)


def _sigmoid_from_log_odds(log_odds: float) -> float:
    if log_odds >= 0:
        z = math.exp(-log_odds)
        return 1.0 / (1.0 + z)
    z = math.exp(log_odds)
    return z / (1.0 + z)


def _to_label(score: float) -> str:
    if score < 0.34:
        return "low"
    if score < 0.67:
        return "medium"
    return "high"


def _feature_tokens(row: CitasFeatureRow) -> dict[str, str]:
    return {
        "duracion_bucket": row.duracion_bucket,
        "notas_len_bucket": row.notas_len_bucket,
        "is_weekend": str(int(row.is_weekend)),
        "estado_norm": row.estado_norm,
        "has_incidencias": str(int(row.has_incidencias)),
        "is_suspicious": str(int(row.is_suspicious)),
    }


def _empty_feature_counts() -> dict[str, dict[str, dict[str, int]]]:
    return {name: {"0": {}, "1": {}} for name in _feature_tokens(_dummy_row()).keys()}


def _feature_value_cardinality(feature_counts: dict[str, dict[str, dict[str, int]]]) -> dict[str, int]:
    cardinality: dict[str, int] = {}
    for feature, per_class in feature_counts.items():
        tokens = set(per_class.get("0", {}).keys()) | set(per_class.get("1", {}).keys())
        cardinality[feature] = max(1, len(tokens))
    return cardinality


def _dummy_row() -> CitasFeatureRow:
    return CitasFeatureRow(
        cita_id="_",
        duracion_min=0,
        duracion_bucket="0-10",
        hora_inicio=0,
        dia_semana=0,
        is_weekend=False,
        notas_len=0,
        notas_len_bucket="0",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=False,
    )

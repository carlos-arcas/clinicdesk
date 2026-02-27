from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.application.features.citas_features import CitasFeatureRow

_DRIFT_FEATURES = ("duracion_bucket", "notas_len_bucket", "is_weekend", "estado_norm", "is_suspicious")
_PSI_ALERT_THRESHOLD = 0.2


@dataclass(slots=True)
class DriftReport:
    from_version: str
    to_version: str
    total_from: int
    total_to: int
    feature_shifts: dict[str, dict[str, float]]
    psi_by_feature: dict[str, float]
    overall_flag: bool


def compute_categorical_distribution(rows: list[CitasFeatureRow], key_fn: Callable[[CitasFeatureRow], str]) -> dict[str, float]:
    if not rows:
        return {}
    counts: dict[str, int] = {}
    for row in rows:
        key = key_fn(row)
        counts[key] = counts.get(key, 0) + 1
    total = len(rows)
    return {key: value / total for key, value in sorted(counts.items())}


def compute_psi(p: dict[str, float], q: dict[str, float], eps: float = 1e-6) -> float:
    psi = 0.0
    for key in sorted(set(p) | set(q)):
        p_i = max(p.get(key, 0.0), eps)
        q_i = max(q.get(key, 0.0), eps)
        psi += (q_i - p_i) * math.log(q_i / p_i)
    return psi


def compute_citas_drift(
    features_from: list[CitasFeatureRow],
    features_to: list[CitasFeatureRow],
    from_version: str = "from",
    to_version: str = "to",
) -> DriftReport:
    feature_shifts: dict[str, dict[str, float]] = {}
    psi_by_feature: dict[str, float] = {}

    for feature_name in _DRIFT_FEATURES:
        p = compute_categorical_distribution(features_from, lambda row, key=feature_name: _token(row, key))
        q = compute_categorical_distribution(features_to, lambda row, key=feature_name: _token(row, key))
        deltas = {token: q.get(token, 0.0) - p.get(token, 0.0) for token in sorted(set(p) | set(q))}
        feature_shifts[feature_name] = deltas
        psi_by_feature[feature_name] = compute_psi(p, q)

    overall_flag = any(score >= _PSI_ALERT_THRESHOLD for score in psi_by_feature.values())
    return DriftReport(
        from_version=from_version,
        to_version=to_version,
        total_from=len(features_from),
        total_to=len(features_to),
        feature_shifts=feature_shifts,
        psi_by_feature=psi_by_feature,
        overall_flag=overall_flag,
    )


def _token(row: CitasFeatureRow, key: str) -> str:
    value = getattr(row, key)
    if isinstance(value, bool):
        return str(int(value))
    return str(value)

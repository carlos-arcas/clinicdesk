from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ml.evaluation import EvalMetrics


@dataclass(slots=True)
class ThresholdPolicy:
    threshold: float
    objective: str
    value: float


def compute_metrics_at_threshold(scores: list[float], y_true: list[int], thr: float) -> EvalMetrics:
    _validate_inputs(scores, y_true)
    tp = fp = tn = fn = 0
    for score, target in zip(scores, y_true):
        predicted = 1 if score >= thr else 0
        if predicted == 1 and target == 1:
            tp += 1
        elif predicted == 1 and target == 0:
            fp += 1
        elif predicted == 0 and target == 0:
            tn += 1
        else:
            fn += 1
    return _build_metrics(tp, fp, tn, fn)


def calibrate_threshold(scores: list[float], y_true: list[int], policy: ThresholdPolicy) -> float:
    metrics_by_thr = _metrics_grid(scores, y_true)
    objective = policy.objective.strip().lower()
    if objective == "f1_max":
        return _best_by_f1(metrics_by_thr)
    if objective == "min_recall":
        return _best_with_min_target(metrics_by_thr, policy.value, key_name="recall")
    if objective == "min_precision":
        return _best_with_min_target(metrics_by_thr, policy.value, key_name="precision")
    raise ValueError("objective inválido. Use: min_recall|min_precision|f1_max")


def _validate_inputs(scores: list[float], y_true: list[int]) -> None:
    if len(scores) != len(y_true) or not scores:
        raise ValueError("scores/y_true deben tener mismo tamaño y no estar vacíos.")


def _threshold_candidates(scores: list[float], fallback: float) -> list[float]:
    unique_scores = sorted({round(score, 6) for score in scores if 0.0 <= score <= 1.0})
    if unique_scores:
        return unique_scores
    return [fallback]


def _metrics_grid(scores: list[float], y_true: list[int]) -> list[tuple[float, EvalMetrics, float]]:
    _validate_inputs(scores, y_true)
    candidates = _threshold_candidates(scores, fallback=0.5)
    by_thr: list[tuple[float, EvalMetrics, float]] = []
    for thr in candidates:
        metrics = compute_metrics_at_threshold(scores, y_true, thr)
        by_thr.append((thr, metrics, _f1(metrics)))
    return by_thr


def _best_by_f1(metrics_by_thr: list[tuple[float, EvalMetrics, float]]) -> float:
    best = max(metrics_by_thr, key=lambda item: (item[2], item[1].precision, -item[0]))
    return float(best[0])


def _best_with_min_target(
    metrics_by_thr: list[tuple[float, EvalMetrics, float]], target: float, key_name: str
) -> float:
    compliant = [item for item in metrics_by_thr if getattr(item[1], key_name) >= target]
    if compliant:
        winner = min(compliant, key=lambda item: (-item[1].precision, -item[2], item[0]))
        return float(winner[0])
    fallback = max(
        metrics_by_thr,
        key=lambda item: (getattr(item[1], key_name), item[1].precision, item[2], -item[0]),
    )
    return float(fallback[0])


def _build_metrics(tp: int, fp: int, tn: int, fn: int) -> EvalMetrics:
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return EvalMetrics(accuracy=accuracy, precision=precision, recall=recall, tp=tp, fp=fp, tn=tn, fn=fn)


def _f1(metrics: EvalMetrics) -> float:
    denom = metrics.precision + metrics.recall
    return (2.0 * metrics.precision * metrics.recall / denom) if denom else 0.0

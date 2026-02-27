from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.naive_bayes_citas import TrainedModel, predict_one


@dataclass(slots=True)
class EvalMetrics:
    accuracy: float
    precision: float
    recall: float
    tp: int
    fp: int
    tn: int
    fn: int


def evaluate(
    model: TrainedModel,
    rows: list[CitasFeatureRow],
    target_fn: Callable[[CitasFeatureRow], int],
) -> EvalMetrics:
    tp = fp = tn = fn = 0
    for row in rows:
        target = int(target_fn(row))
        predicted = 1 if predict_one(model, row).score >= 0.5 else 0
        tp, fp, tn, fn = _update_confusion_counts(tp, fp, tn, fn, target, predicted)
    return _build_metrics(tp, fp, tn, fn)


def _update_confusion_counts(
    tp: int, fp: int, tn: int, fn: int, target: int, predicted: int
) -> tuple[int, int, int, int]:
    if predicted == 1 and target == 1:
        return tp + 1, fp, tn, fn
    if predicted == 1 and target == 0:
        return tp, fp + 1, tn, fn
    if predicted == 0 and target == 0:
        return tp, fp, tn + 1, fn
    return tp, fp, tn, fn + 1


def _build_metrics(tp: int, fp: int, tn: int, fn: int) -> EvalMetrics:
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return EvalMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
    )

from __future__ import annotations

from clinicdesk.app.application.ml.calibration import ThresholdPolicy, calibrate_threshold, compute_metrics_at_threshold


def test_calibrate_threshold_min_recall_prioritizes_precision_and_f1() -> None:
    scores = [0.90, 0.80, 0.70, 0.60, 0.40, 0.30]
    y_true = [1, 1, 1, 0, 0, 0]
    policy = ThresholdPolicy(threshold=0.5, objective="min_recall", value=0.66)

    threshold = calibrate_threshold(scores, y_true, policy)
    metrics = compute_metrics_at_threshold(scores, y_true, threshold)

    assert threshold == 0.7
    assert metrics.recall >= 0.66
    assert metrics.precision == 1.0

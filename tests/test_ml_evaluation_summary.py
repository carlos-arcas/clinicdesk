from __future__ import annotations

import json
from pathlib import Path

from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.usecases.export_evaluation_summary import EvaluationSummaryData, ExportEvaluationSummary


def test_export_evaluation_summary_generates_json_and_markdown(tmp_path: Path) -> None:
    data = EvaluationSummaryData(
        model_name="citas_nb_v1",
        model_version="m_demo",
        dataset_version="v_demo",
        predictor_kind="trained",
        trained_on_dataset_version="v_demo",
        created_at="2026-01-01T00:00:00+00:00",
        calibrated_threshold=0.41,
        train_metrics=EvalMetrics(0.91, 0.82, 0.87, 41, 9, 73, 6),
        test_metrics=EvalMetrics(0.79, 0.69, 0.56, 9, 4, 12, 7),
        calibrated_test_metrics=EvalMetrics(0.75, 0.60, 0.72, 11, 7, 9, 5),
        test_row_count=32,
        evaluation_note="offline eval with deterministic temporal holdout (proxy label)",
    )

    outputs = ExportEvaluationSummary().execute(data, tmp_path)

    assert outputs["json"].exists()
    assert outputs["markdown"].exists()

    payload = json.loads(outputs["json"].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "ml_eval_summary_v1"
    assert payload["context"]["dataset_version"] == "v_demo"
    assert payload["metrics"]["test_calibrated"]["recall"] == 0.72
    assert "predictor baseline" in payload["interpretation"][0]

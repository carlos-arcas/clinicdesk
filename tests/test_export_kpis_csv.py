from __future__ import annotations

import csv
from pathlib import Path

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.usecases.export_kpis_csv import ExportKpisCSV, ExportKpisRequest
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse


def test_export_kpis_csv_generates_expected_files_and_headers(tmp_path: Path) -> None:
    exporter = ExportKpisCSV()
    outputs = exporter.execute(_request(tmp_path, 0.08))

    assert set(outputs) == {
        "kpi_overview",
        "kpi_scores_by_bucket",
        "kpi_drift_by_feature",
        "kpi_training_metrics",
    }
    overview = _read_csv(Path(outputs["kpi_overview"]))
    assert overview[0] == [
        "run_ts",
        "dataset_version",
        "model_name",
        "model_version",
        "predictor_kind",
        "citas_count",
        "risk_high_count",
        "risk_high_pct",
        "threshold_used",
        "drift_severity",
        "drift_psi_max",
        "exports_dir",
    ]
    assert overview[1][9] == "GREEN"


def test_export_kpis_csv_sets_severity_red_when_psi_is_high(tmp_path: Path) -> None:
    outputs = ExportKpisCSV().execute(_request(tmp_path, 0.25))

    overview = _read_csv(Path(outputs["kpi_overview"]))
    drift = _read_csv(Path(outputs["kpi_drift_by_feature"]))
    assert overview[1][9] == "RED"
    assert drift[1][4] == "RED"


def _request(tmp_path: Path, psi_value: float) -> ExportKpisRequest:
    return ExportKpisRequest(
        dataset_version="ds_v1",
        predictor_kind="trained",
        exports_dir=tmp_path,
        train_response=TrainCitasModelResponse(
            model_name="citas_nb_v1",
            model_version="m_v1",
            dataset_version="ds_v1",
            train_metrics=EvalMetrics(0.9, 0.8, 0.85, 9, 1, 8, 2),
            test_metrics=EvalMetrics(0.8, 0.75, 0.7, 7, 2, 6, 3),
            calibrated_threshold=0.61,
            test_metrics_at_calibrated_threshold=EvalMetrics(0.8, 0.75, 0.7, 7, 2, 6, 3),
        ),
        score_response=ScoreCitasResponse(
            version="ds_v1",
            total=3,
            items=[
                ScoredCita("c1", 0.81, "risk", ["a"]),
                ScoredCita("c2", 0.22, "no_risk", ["b"]),
                ScoredCita("c3", 0.76, "risk", ["c"]),
            ],
        ),
        drift_report=DriftReport(
            from_version="ds_prev",
            to_version="ds_v1",
            total_from=10,
            total_to=10,
            feature_shifts={},
            psi_by_feature={"duracion_bucket": psi_value},
            overall_flag=psi_value >= 0.2,
        ),
        run_ts="2026-01-01T00:00:00+00:00",
    )


def _read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))

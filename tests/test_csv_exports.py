from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.usecases.export_csv import (
    ExportDriftCSV,
    ExportFeaturesCSV,
    ExportModelMetricsCSV,
    ExportScoringCSV,
)
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse


def test_export_features_csv_creates_expected_header_and_rows(tmp_path: Path) -> None:
    rows = [
        CitasFeatureRow("c1", 30, "21-40", 10, 2, False, 5, "1-20", False, "programada", False),
        CitasFeatureRow("c2", 45, "41+", 9, 6, True, 0, "0", False, "no_show", True),
    ]

    output_file = ExportFeaturesCSV().execute("v1", rows, tmp_path)

    assert output_file.exists()
    loaded = _read_csv(output_file)
    assert loaded[0] == [
        "dataset_version",
        "cita_id",
        "duracion_bucket",
        "notas_len_bucket",
        "is_weekend",
        "estado_norm",
        "is_suspicious",
        "target_proxy",
    ]
    assert len(loaded) == 3


def test_export_model_metrics_csv_respects_column_order(tmp_path: Path) -> None:
    metrics = TrainCitasModelResponse(
        model_name="citas_nb_v1",
        model_version="m1",
        dataset_version="v1",
        train_metrics=EvalMetrics(0.9, 0.8, 0.85, 8, 2, 10, 1),
        test_metrics=EvalMetrics(0.8, 0.75, 0.7, 7, 3, 6, 2),
        calibrated_threshold=0.42,
        test_metrics_at_calibrated_threshold=EvalMetrics(0.8, 0.75, 0.7, 7, 3, 6, 2),
    )

    output_file = ExportModelMetricsCSV().execute(metrics, tmp_path)

    loaded = _read_csv(output_file)
    assert loaded[0] == [
        "model_name",
        "model_version",
        "dataset_version",
        "train_accuracy",
        "test_accuracy",
        "train_precision",
        "test_precision",
        "train_recall",
        "test_recall",
        "calibrated_threshold",
        "created_at",
    ]


def test_export_scoring_csv_writes_threshold_used(tmp_path: Path) -> None:
    response = ScoreCitasResponse(
        version="v2",
        total=1,
        items=[ScoredCita(cita_id="c-1", score=0.73, label="risk", reasons=["x"])],
    )

    output_file = ExportScoringCSV().execute(response, "trained", "m2", 0.61, tmp_path)

    loaded = _read_csv(output_file)
    assert loaded[1][6] == "0.610000"


def test_export_drift_csv_generates_one_row_per_feature(tmp_path: Path) -> None:
    report = DriftReport(
        from_version="v1",
        to_version="v2",
        total_from=10,
        total_to=10,
        feature_shifts={},
        psi_by_feature={"duracion_bucket": 0.21, "estado_norm": 0.03, "is_weekend": 0.12},
        overall_flag=True,
    )

    output_file = ExportDriftCSV().execute(report, tmp_path)

    loaded = _read_csv(output_file)
    assert len(loaded) == 4


def test_cli_export_smoke_creates_csv_in_tmp_path(tmp_path: Path) -> None:
    cli = _load_ml_cli_module()
    feature_store = str(tmp_path / "feature_store")
    model_store = str(tmp_path / "model_store")
    exports = str(tmp_path / "exports")

    assert cli.main(["build-features", "--demo-fake", "--version", "v_demo", "--store-path", feature_store]) == 0
    assert (
        cli.main(
            [
                "train",
                "--dataset-version",
                "v_demo",
                "--model-version",
                "m_demo",
                "--feature-store-path",
                feature_store,
                "--model-store-path",
                model_store,
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "export",
                "metrics",
                "--model-version",
                "m_demo",
                "--dataset-version",
                "v_demo",
                "--model-store-path",
                model_store,
                "--output",
                exports,
            ]
        )
        == 0
    )
    assert (tmp_path / "exports" / "model_metrics_export.csv").exists()


def _read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def _load_ml_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "ml_cli.py"
    spec = importlib.util.spec_from_file_location("scripts.ml_cli", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

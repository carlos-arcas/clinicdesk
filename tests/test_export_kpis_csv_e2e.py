from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest


EXPECTED_EXPORTS = {
    "kpi_overview.csv",
    "kpi_scores_by_bucket.csv",
    "kpi_drift_by_feature.csv",
    "kpi_training_metrics.csv",
}


@pytest.fixture()
def ml_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "ml_cli.py"
    spec = importlib.util.spec_from_file_location("scripts.ml_cli", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_kpis_cli_trained_with_drift_generates_contractual_csvs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ml_cli_module,
) -> None:
    rutas = _prepare_operational_pipeline(tmp_path, monkeypatch, ml_cli_module)
    export_dir = rutas["exports_trained"]

    _run_cli(
        ml_cli_module,
        [
            "export",
            "kpis",
            "--dataset-version",
            "ds_shifted",
            "--model-version",
            "m_shifted",
            "--predictor",
            "trained",
            "--from-version",
            "ds_base",
            "--feature-store-path",
            rutas["feature_store"],
            "--model-store-path",
            rutas["model_store"],
            "--output",
            export_dir,
        ],
    )

    _assert_expected_exports(Path(export_dir))
    overview = _read_csv(Path(export_dir) / "kpi_overview.csv")
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
    assert len(overview) == 2
    assert overview[1][1] == "ds_shifted"
    assert overview[1][2] == "citas_nb_v1"
    assert overview[1][3] == "m_shifted"
    assert overview[1][4] == "trained"
    assert int(overview[1][5]) > 0
    assert int(overview[1][6]) >= 0
    assert 0.0 <= float(overview[1][7]) <= 1.0
    assert float(overview[1][8]) > 0.0
    assert overview[1][9] in {"GREEN", "AMBER", "RED"}
    assert float(overview[1][10]) >= 0.0
    assert overview[1][11] == export_dir

    buckets = _read_csv(Path(export_dir) / "kpi_scores_by_bucket.csv")
    assert buckets[0] == ["dataset_version", "model_version", "predictor_kind", "label", "count", "pct"]
    assert len(buckets) >= 2
    etiquetas = {fila[3] for fila in buckets[1:]}
    assert etiquetas <= {"risk", "no_risk"}
    for fila in buckets[1:]:
        assert fila[0] == "ds_shifted"
        assert fila[1] == "m_shifted"
        assert fila[2] == "trained"
        assert int(fila[4]) >= 0
        assert 0.0 <= float(fila[5]) <= 1.0

    drift = _read_csv(Path(export_dir) / "kpi_drift_by_feature.csv")
    assert drift[0] == ["from_version", "to_version", "feature_name", "psi_value", "severity"]
    assert len(drift) >= 2
    for fila in drift[1:]:
        assert fila[0] == "ds_base"
        assert fila[1] == "ds_shifted"
        assert fila[2]
        assert float(fila[3]) >= 0.0
        assert fila[4] in {"GREEN", "AMBER", "RED"}

    training = _read_csv(Path(export_dir) / "kpi_training_metrics.csv")
    assert training[0] == ["model_name", "model_version", "dataset_version", "split", "metric_name", "metric_value"]
    assert len(training) == 9
    assert {fila[1] for fila in training[1:]} == {"m_shifted"}
    assert {fila[2] for fila in training[1:]} == {"ds_shifted"}
    assert {fila[3] for fila in training[1:]} == {"train", "test"}
    assert {fila[4] for fila in training[1:]} == {"accuracy", "precision", "recall", "f1"}
    assert all(float(fila[5]) >= 0.0 for fila in training[1:])


def test_export_kpis_cli_baseline_without_drift_keeps_contractual_consistency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ml_cli_module,
) -> None:
    rutas = _prepare_operational_pipeline(tmp_path, monkeypatch, ml_cli_module)
    export_dir = rutas["exports_baseline"]

    _run_cli(
        ml_cli_module,
        [
            "export",
            "kpis",
            "--dataset-version",
            "ds_shifted",
            "--model-version",
            "m_shifted",
            "--predictor",
            "baseline",
            "--feature-store-path",
            rutas["feature_store"],
            "--model-store-path",
            rutas["model_store"],
            "--output",
            export_dir,
        ],
    )

    overview = _read_csv(Path(export_dir) / "kpi_overview.csv")
    drift = _read_csv(Path(export_dir) / "kpi_drift_by_feature.csv")
    buckets = _read_csv(Path(export_dir) / "kpi_scores_by_bucket.csv")

    assert overview[1][1] == "ds_shifted"
    assert overview[1][3] == "m_shifted"
    assert overview[1][4] == "baseline"
    assert overview[1][9] == "GREEN"
    assert overview[1][10] == "0.000000"
    assert drift == [["from_version", "to_version", "feature_name", "psi_value", "severity"]]
    assert len(buckets) >= 2
    assert {fila[2] for fila in buckets[1:]} == {"baseline"}


def test_export_kpis_cli_returns_explicit_error_for_inconsistent_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ml_cli_module,
) -> None:
    rutas = _prepare_operational_pipeline(tmp_path, monkeypatch, ml_cli_module)

    rc = ml_cli_module.main(
        [
            "export",
            "kpis",
            "--dataset-version",
            "ds_base",
            "--model-version",
            "m_shifted",
            "--predictor",
            "trained",
            "--feature-store-path",
            rutas["feature_store"],
            "--model-store-path",
            rutas["model_store"],
            "--output",
            str(tmp_path / "exports_error"),
        ]
    )

    assert rc == 2


def _prepare_operational_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cli,
) -> dict[str, str]:
    sqlite_path_base = tmp_path / "demo_base.sqlite"
    sqlite_path_shifted = tmp_path / "demo_shifted.sqlite"
    feature_store = str(tmp_path / "feature_store")
    model_store = str(tmp_path / "model_store")
    _seed_and_build_dataset(
        cli, monkeypatch, sqlite_path_base, feature_store, 321, "2026-01-01", "2026-01-31", "ds_base"
    )
    _seed_and_build_dataset(
        cli, monkeypatch, sqlite_path_shifted, feature_store, 654, "2026-02-01", "2026-02-28", "ds_shifted"
    )
    _run_cli(
        cli,
        [
            "train",
            "--dataset-version",
            "ds_shifted",
            "--model-version",
            "m_shifted",
            "--feature-store-path",
            feature_store,
            "--model-store-path",
            model_store,
        ],
    )
    _run_cli(
        cli,
        [
            "score",
            "--dataset-version",
            "ds_shifted",
            "--predictor",
            "trained",
            "--model-version",
            "m_shifted",
            "--feature-store-path",
            feature_store,
            "--model-store-path",
            model_store,
        ],
    )
    return {
        "sqlite_path": str(sqlite_path_shifted),
        "feature_store": feature_store,
        "model_store": model_store,
        "exports_trained": str(tmp_path / "exports_trained"),
        "exports_baseline": str(tmp_path / "exports_baseline"),
    }


def _seed_and_build_dataset(
    cli,
    monkeypatch: pytest.MonkeyPatch,
    sqlite_path: Path,
    feature_store: str,
    seed: int,
    from_date: str,
    to_date: str,
    dataset_version: str,
) -> None:
    monkeypatch.setenv("CLINICDESK_DB_PATH", str(sqlite_path))
    _run_cli(
        cli,
        [
            "seed-demo",
            "--seed",
            str(seed),
            "--doctors",
            "4",
            "--patients",
            "12",
            "--appointments",
            "90",
            "--from",
            from_date,
            "--to",
            to_date,
            "--incidence-rate",
            "0.35",
            "--sqlite-path",
            str(sqlite_path),
        ],
    )
    _run_cli(
        cli,
        [
            "build-features",
            "--version",
            dataset_version,
            "--from",
            from_date,
            "--to",
            to_date,
            "--store-path",
            feature_store,
        ],
    )


def _run_cli(cli, argv: list[str]) -> None:
    assert cli.main(argv) == 0


def _assert_expected_exports(export_dir: Path) -> None:
    assert {path.name for path in export_dir.iterdir()} == EXPECTED_EXPORTS


def _read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.ml.drift_explain import DriftSeverity, explain_drift, severity_from_psi
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse


@dataclass(slots=True, frozen=True)
class ExportKpisRequest:
    dataset_version: str
    predictor_kind: str
    exports_dir: str | Path
    train_response: TrainCitasModelResponse
    score_response: ScoreCitasResponse
    drift_report: DriftReport | None
    run_ts: str | None = None


class ExportKpisCSV:
    OVERVIEW_FILE = "kpi_overview.csv"
    BUCKET_FILE = "kpi_scores_by_bucket.csv"
    DRIFT_FILE = "kpi_drift_by_feature.csv"
    TRAINING_FILE = "kpi_training_metrics.csv"

    def execute(self, request: ExportKpisRequest) -> dict[str, str]:
        output_dir = _resolve_output_dir(request.exports_dir)
        run_ts = request.run_ts or _utc_now()
        labels = Counter(item.label for item in request.score_response.items)
        total = max(request.score_response.total, 1)
        high_count = labels.get("risk", 0)
        high_pct = high_count / total
        drift_severity, _, psi_max = _resolve_drift(request.drift_report)
        _write_csv(output_dir / self.OVERVIEW_FILE, _overview_header(), [_overview_row(request, run_ts, high_count, high_pct, drift_severity, psi_max)])
        _write_csv(output_dir / self.BUCKET_FILE, _bucket_header(), _bucket_rows(request, labels))
        _write_csv(output_dir / self.DRIFT_FILE, _drift_header(), _drift_rows(request.drift_report))
        _write_csv(output_dir / self.TRAINING_FILE, _training_header(), _training_rows(request.train_response))
        return {
            "kpi_overview": (output_dir / self.OVERVIEW_FILE).as_posix(),
            "kpi_scores_by_bucket": (output_dir / self.BUCKET_FILE).as_posix(),
            "kpi_drift_by_feature": (output_dir / self.DRIFT_FILE).as_posix(),
            "kpi_training_metrics": (output_dir / self.TRAINING_FILE).as_posix(),
        }


def _overview_header() -> tuple[str, ...]:
    return (
        "run_ts", "dataset_version", "model_name", "model_version", "predictor_kind", "citas_count", "risk_high_count",
        "risk_high_pct", "threshold_used", "drift_severity", "drift_psi_max", "exports_dir",
    )


def _overview_row(
    request: ExportKpisRequest,
    run_ts: str,
    high_count: int,
    high_pct: float,
    drift_severity: DriftSeverity,
    psi_max: float,
) -> tuple[str, ...]:
    return (
        run_ts,
        request.dataset_version,
        request.train_response.model_name,
        request.train_response.model_version,
        request.predictor_kind,
        str(request.score_response.total),
        str(high_count),
        _fmt(high_pct),
        _fmt(request.train_response.calibrated_threshold),
        drift_severity.value,
        _fmt(psi_max),
        str(request.exports_dir),
    )


def _bucket_header() -> tuple[str, ...]:
    return ("dataset_version", "model_version", "predictor_kind", "label", "count", "pct")


def _bucket_rows(request: ExportKpisRequest, labels: Counter[str]) -> list[tuple[str, ...]]:
    total = max(request.score_response.total, 1)
    rows: list[tuple[str, ...]] = []
    for label in sorted(labels):
        count = labels[label]
        rows.append((request.dataset_version, request.train_response.model_version, request.predictor_kind, label, str(count), _fmt(count / total)))
    return rows


def _drift_header() -> tuple[str, ...]:
    return ("from_version", "to_version", "feature_name", "psi_value", "severity")


def _drift_rows(report: DriftReport | None) -> list[tuple[str, ...]]:
    if report is None:
        return []
    rows: list[tuple[str, ...]] = []
    for feature_name, psi in sorted(report.psi_by_feature.items()):
        rows.append((report.from_version, report.to_version, feature_name, _fmt(psi), severity_from_psi(float(psi)).value))
    return rows


def _training_header() -> tuple[str, ...]:
    return ("model_name", "model_version", "dataset_version", "split", "metric_name", "metric_value")


def _training_rows(train_response: TrainCitasModelResponse) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for split, values in (("train", train_response.train_metrics), ("test", train_response.test_metrics)):
        rows.append(_training_metric_row(train_response, split, "accuracy", float(values.accuracy)))
        rows.append(_training_metric_row(train_response, split, "precision", float(values.precision)))
        rows.append(_training_metric_row(train_response, split, "recall", float(values.recall)))
        rows.append(_training_metric_row(train_response, split, "f1", _f1(values.precision, values.recall)))
    return rows


def _training_metric_row(
    train_response: TrainCitasModelResponse,
    split: str,
    metric_name: str,
    metric_value: float,
) -> tuple[str, ...]:
    return (
        train_response.model_name,
        train_response.model_version,
        train_response.dataset_version,
        split,
        metric_name,
        _fmt(metric_value),
    )


def _f1(precision: float, recall: float) -> float:
    total = precision + recall
    if total == 0:
        return 0.0
    return 2 * precision * recall / total


def _resolve_drift(report: DriftReport | None) -> tuple[DriftSeverity, str, float]:
    if report is None:
        return DriftSeverity.GREEN, "", 0.0
    return explain_drift(report)


def _resolve_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _write_csv(path: Path, headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _fmt(value: float) -> str:
    return f"{value:.6f}"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()

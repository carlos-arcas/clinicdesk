from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.drift import DriftReport
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse

class ExportFeaturesCSV:
    FILE_NAME = "features_export.csv"
    COLUMNS = (
        "dataset_version",
        "cita_id",
        "duracion_bucket",
        "notas_len_bucket",
        "is_weekend",
        "estado_norm",
        "is_suspicious",
        "target_proxy",
    )

    def execute(
        self,
        dataset_version: str,
        features: Iterable[CitasFeatureRow | dict[str, Any]],
        output_path: str | Path,
    ) -> Path:
        output_file = _resolve_output_file(output_path, self.FILE_NAME)
        rows = [self._to_row(dataset_version, _to_feature_row(feature)) for feature in features]
        _write_csv(output_file, self.COLUMNS, rows)
        return output_file

    def _to_row(self, dataset_version: str, feature: CitasFeatureRow) -> tuple[str, ...]:
        return (
            dataset_version,
            feature.cita_id,
            feature.duracion_bucket,
            feature.notas_len_bucket,
            _bool_token(feature.is_weekend),
            feature.estado_norm,
            _bool_token(feature.is_suspicious),
            "1" if feature.is_suspicious else "0",
        )


class ExportModelMetricsCSV:
    FILE_NAME = "model_metrics_export.csv"
    COLUMNS = (
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
    )

    def execute(self, metrics: TrainCitasModelResponse, output_path: str | Path) -> Path:
        output_file = _resolve_output_file(output_path, self.FILE_NAME)
        row = (
            metrics.model_name,
            metrics.model_version,
            metrics.dataset_version,
            _fmt_float(metrics.train_metrics.accuracy),
            _fmt_float(metrics.test_metrics.accuracy),
            _fmt_float(metrics.train_metrics.precision),
            _fmt_float(metrics.test_metrics.precision),
            _fmt_float(metrics.train_metrics.recall),
            _fmt_float(metrics.test_metrics.recall),
            _fmt_float(metrics.calibrated_threshold),
            "",
        )
        _write_csv(output_file, self.COLUMNS, [row])
        return output_file


@dataclass(slots=True)
class ModelMetricsExportData:
    model_name: str
    model_version: str
    dataset_version: str
    train_accuracy: float
    test_accuracy: float
    train_precision: float
    test_precision: float
    train_recall: float
    test_recall: float
    calibrated_threshold: float
    created_at: str


class ExportModelMetricsFromMetadataCSV:
    FILE_NAME = ExportModelMetricsCSV.FILE_NAME
    COLUMNS = ExportModelMetricsCSV.COLUMNS

    def execute(self, data: ModelMetricsExportData, output_path: str | Path) -> Path:
        output_file = _resolve_output_file(output_path, self.FILE_NAME)
        row = (
            data.model_name,
            data.model_version,
            data.dataset_version,
            _fmt_float(data.train_accuracy),
            _fmt_float(data.test_accuracy),
            _fmt_float(data.train_precision),
            _fmt_float(data.test_precision),
            _fmt_float(data.train_recall),
            _fmt_float(data.test_recall),
            _fmt_float(data.calibrated_threshold),
            data.created_at,
        )
        _write_csv(output_file, self.COLUMNS, [row])
        return output_file


class ExportScoringCSV:
    FILE_NAME = "scoring_export.csv"
    COLUMNS = (
        "dataset_version",
        "model_version",
        "predictor_kind",
        "cita_id",
        "score",
        "label",
        "threshold_used",
    )

    def execute(
        self,
        scoring: ScoreCitasResponse,
        predictor_kind: str,
        model_version: str,
        threshold_used: float,
        output_path: str | Path,
    ) -> Path:
        output_file = _resolve_output_file(output_path, self.FILE_NAME)
        rows = [
            (
                scoring.version,
                model_version,
                predictor_kind,
                item.cita_id,
                _fmt_float(item.score),
                item.label,
                _fmt_float(threshold_used),
            )
            for item in scoring.items
        ]
        _write_csv(output_file, self.COLUMNS, rows)
        return output_file


class ExportDriftCSV:
    FILE_NAME = "drift_export.csv"
    COLUMNS = ("from_version", "to_version", "feature_name", "psi_value", "overall_flag")

    def execute(self, report: DriftReport, output_path: str | Path) -> Path:
        output_file = _resolve_output_file(output_path, self.FILE_NAME)
        rows = [
            (
                report.from_version,
                report.to_version,
                feature_name,
                _fmt_float(psi),
                _bool_token(report.overall_flag),
            )
            for feature_name, psi in sorted(report.psi_by_feature.items())
        ]
        _write_csv(output_file, self.COLUMNS, rows)
        return output_file


def _resolve_output_file(output_path: str | Path, file_name: str) -> Path:
    base_path = Path(output_path)
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / file_name


def _write_csv(output_file: Path, columns: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def _fmt_float(value: float) -> str:
    return f"{value:.6f}"


def _bool_token(value: bool) -> str:
    return "1" if value else "0"


def _to_feature_row(raw: CitasFeatureRow | dict[str, Any]) -> CitasFeatureRow:
    if isinstance(raw, CitasFeatureRow):
        return raw
    return CitasFeatureRow(**raw)

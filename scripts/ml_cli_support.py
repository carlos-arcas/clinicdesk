from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta

from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.ports.citas_read_port import CitaReadModel, CitasReadPort
from clinicdesk.app.application.usecases.export_csv import ModelMetricsExportData
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse
from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.infrastructure.sqlite.citas_read_adapter import SqliteCitasReadAdapter
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository

_DEFAULT_MODEL_NAME = "citas_nb_v1"


class FakeCitasReadAdapter(CitasReadPort):
    def __init__(self, rows: list[CitaReadModel]) -> None:
        self._rows = rows

    def list_in_range(self, desde: datetime, hasta: datetime) -> list[CitaReadModel]:
        return [row for row in self._rows if desde <= row.inicio <= hasta]


def resolve_range(from_date: str | None, to_date: str | None) -> tuple[datetime, datetime]:
    now = datetime.now().replace(microsecond=0)
    default_from = now - timedelta(days=30)
    desde = parse_date(from_date, default=default_from)
    hasta = parse_date(to_date, default=now)
    if hasta < desde:
        raise ValueError("Rango inválido: --to no puede ser menor que --from")
    return desde, hasta


def parse_date(raw: str | None, *, default: datetime) -> datetime:
    if not raw:
        return default
    return datetime.strptime(raw, "%Y-%m-%d")


def build_read_adapter(demo_fake: bool, demo_profile: str, desde: datetime) -> CitasReadPort:
    if demo_fake:
        return FakeCitasReadAdapter(make_fake_citas(demo_profile, desde, 40))
    try:
        connection = bootstrap_database(apply_schema=True)
        return SqliteCitasReadAdapter(CitasRepository(connection), IncidenciasRepository(connection))
    except sqlite3.Error:
        return FakeCitasReadAdapter(make_fake_citas(demo_profile, desde, 40))


def make_fake_citas(profile: str, start: datetime, total: int) -> list[CitaReadModel]:
    return [_fake_cita(profile, start, idx) for idx in range(total)]


def _fake_cita(profile: str, start: datetime, idx: int) -> CitaReadModel:
    inicio = start + timedelta(hours=idx * 3)
    duration = 15 + (idx % 4) * 10
    if profile == "shifted":
        duration += 30
    estado = "no_show" if profile == "shifted" and idx % 3 == 0 else "programada"
    return CitaReadModel(
        cita_id=f"demo-{profile}-{idx}",
        paciente_id=1000 + idx,
        medico_id=200 + (idx % 3),
        inicio=inicio,
        fin=inicio + timedelta(minutes=duration),
        estado=estado,
        notas=("nota extensa " * 4 if profile == "shifted" else "nota breve").strip(),
        has_incidencias=(idx % (2 if profile == "shifted" else 5) == 0),
    )


def build_train_response_from_metadata(dataset_version: str, model_version: str, metadata: dict) -> TrainCitasModelResponse:
    train_metrics = metadata.get("train_metrics", {})
    test_metrics = metadata.get("test_metrics", {})
    calibrated_metrics = metadata.get("test_metrics_at_calibrated_threshold", test_metrics)
    return TrainCitasModelResponse(
        model_name=_DEFAULT_MODEL_NAME,
        model_version=model_version,
        dataset_version=dataset_version,
        train_metrics=metrics_from_dict(train_metrics),
        test_metrics=metrics_from_dict(test_metrics),
        calibrated_threshold=float(metadata.get("calibrated_threshold", 0.5)),
        test_metrics_at_calibrated_threshold=metrics_from_dict(calibrated_metrics),
    )


def metrics_from_dict(values: dict) -> EvalMetrics:
    return EvalMetrics(
        accuracy=float(values.get("accuracy", 0.0)),
        precision=float(values.get("precision", 0.0)),
        recall=float(values.get("recall", 0.0)),
        tp=int(values.get("tp", 0)),
        fp=int(values.get("fp", 0)),
        tn=int(values.get("tn", 0)),
        fn=int(values.get("fn", 0)),
    )


def build_metrics_export_data(args: argparse.Namespace, metadata: dict) -> ModelMetricsExportData:
    train_metrics = metadata.get("train_metrics", {})
    test_metrics = metadata.get("test_metrics", {})
    return ModelMetricsExportData(
        model_name=args.model_name,
        model_version=args.model_version,
        dataset_version=args.dataset_version,
        train_accuracy=float(train_metrics.get("accuracy", 0.0)),
        test_accuracy=float(test_metrics.get("accuracy", 0.0)),
        train_precision=float(train_metrics.get("precision", 0.0)),
        test_precision=float(test_metrics.get("precision", 0.0)),
        train_recall=float(train_metrics.get("recall", 0.0)),
        test_recall=float(test_metrics.get("recall", 0.0)),
        calibrated_threshold=float(metadata.get("calibrated_threshold", 0.5)),
        created_at=str(metadata.get("created_at", "")),
    )


def add_export_parser(
    subparsers: argparse._SubParsersAction,
    default_feature_store_path: str,
    default_model_store_path: str,
    default_model_name: str,
) -> None:
    parser = subparsers.add_parser("export", help="Exporta contratos CSV para Power BI")
    export_subparsers = parser.add_subparsers(dest="export_command", required=True)

    features_parser = export_subparsers.add_parser("features", help="Exporta dataset de features")
    features_parser.add_argument("--dataset-version", required=True)
    features_parser.add_argument("--output", required=True)
    features_parser.add_argument("--feature-store-path", default=default_feature_store_path)

    metrics_parser = export_subparsers.add_parser("metrics", help="Exporta métricas del modelo")
    metrics_parser.add_argument("--model-name", default=default_model_name)
    metrics_parser.add_argument("--model-version", required=True)
    metrics_parser.add_argument("--dataset-version", required=True)
    metrics_parser.add_argument("--output", required=True)
    metrics_parser.add_argument("--model-store-path", default=default_model_store_path)

    scoring_parser = export_subparsers.add_parser("scoring", help="Exporta scoring")
    scoring_parser.add_argument("--dataset-version", required=True)
    scoring_parser.add_argument("--predictor", choices=("baseline", "trained"), default="trained")
    scoring_parser.add_argument("--model-version", required=True)
    scoring_parser.add_argument("--output", required=True)
    scoring_parser.add_argument("--feature-store-path", default=default_feature_store_path)
    scoring_parser.add_argument("--model-store-path", default=default_model_store_path)

    drift_parser = export_subparsers.add_parser("drift", help="Exporta drift entre versiones")
    drift_parser.add_argument("--from-version", required=True)
    drift_parser.add_argument("--to-version", required=True)
    drift_parser.add_argument("--output", required=True)
    drift_parser.add_argument("--feature-store-path", default=default_feature_store_path)

    kpis_parser = export_subparsers.add_parser("kpis", help="Exporta CSV agregados KPI")
    kpis_parser.add_argument("--dataset-version", required=True)
    kpis_parser.add_argument("--model-version", required=True)
    kpis_parser.add_argument("--predictor", choices=("baseline", "trained"), default="trained")
    kpis_parser.add_argument("--from-version", default=None)
    kpis_parser.add_argument("--output", required=True)
    kpis_parser.add_argument("--feature-store-path", default=default_feature_store_path)
    kpis_parser.add_argument("--model-store-path", default=default_model_store_path)

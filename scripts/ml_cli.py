from __future__ import annotations

import argparse
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence

from clinicdesk.app.application.features.citas_features import build_citas_features, compute_citas_quality_report
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.pipelines.build_citas_dataset import BuildCitasDataset
from clinicdesk.app.application.ports.citas_read_port import CitaReadModel, CitasReadPort
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.drift_citas_features import DriftCitasFeatures, DriftCitasFeaturesRequest
from clinicdesk.app.application.usecases.export_csv import (
    ExportDriftCSV,
    ExportFeaturesCSV,
    ExportModelMetricsFromMetadataCSV,
    ExportScoringCSV,
    ModelMetricsExportData,
)
from clinicdesk.app.application.usecases.score_citas import ScoreCitas, ScoreCitasRequest
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoData, SeedDemoDataRequest
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModel, TrainCitasModelRequest
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import LocalJsonFeatureStore
from clinicdesk.app.infrastructure.model_store.local_json_model_store import LocalJsonModelStore
from clinicdesk.app.infrastructure.sqlite.demo_data_seeder import DemoDataSeeder
from clinicdesk.app.infrastructure.sqlite.reset_safety import (
    UnsafeDatabaseResetError,
    is_safe_demo_db_path,
    reset_demo_database,
)
from clinicdesk.app.infrastructure.sqlite.sqlite_tuning import sqlite_seed_turbo
from clinicdesk.app.infrastructure.sqlite.citas_read_adapter import SqliteCitasReadAdapter
from clinicdesk.app.infrastructure.sqlite.repos_citas import CitasRepository
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import IncidenciasRepository
from clinicdesk.app.bootstrap import bootstrap_database, resolve_db_path
from clinicdesk.app.bootstrap_logging import configure_logging, get_logger, log_soft_exception, set_run_context
from clinicdesk.app.crash_handler import install_global_exception_hook

_DEFAULT_FEATURE_STORE_PATH = "./data/feature_store"
_DEFAULT_MODEL_STORE_PATH = "./data/model_store"
_DEFAULT_MODEL_NAME = "citas_nb_v1"
_LOGGER = get_logger(__name__)


class FakeCitasReadAdapter(CitasReadPort):
    def __init__(self, rows: list[CitaReadModel]) -> None:
        self._rows = rows

    def list_in_range(self, desde: datetime, hasta: datetime) -> list[CitaReadModel]:
        return [row for row in self._rows if desde <= row.inicio <= hasta]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI ML mínima para flujo end-to-end de citas")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_build_features_parser(subparsers)
    _add_train_parser(subparsers)
    _add_score_parser(subparsers)
    _add_drift_parser(subparsers)
    _add_export_parser(subparsers)
    _add_seed_demo_parser(subparsers)
    return parser


def _add_build_features_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("build-features", help="Construye features y artifacts")
    parser.add_argument("--from", dest="from_date", type=str, default=None)
    parser.add_argument("--to", dest="to_date", type=str, default=None)
    parser.add_argument("--version", type=str, default=None)
    parser.add_argument("--store-path", type=str, default=_DEFAULT_FEATURE_STORE_PATH)
    parser.add_argument("--demo-fake", action="store_true")
    parser.add_argument("--demo-profile", choices=("baseline", "shifted"), default="baseline")


def _add_train_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("train", help="Entrena y registra modelo")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--model-name", default=_DEFAULT_MODEL_NAME)
    parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)
    parser.add_argument("--model-store-path", default=_DEFAULT_MODEL_STORE_PATH)


def _add_score_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("score", help="Scoring baseline o entrenado")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--predictor", choices=("baseline", "trained"), default="baseline")
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--model-name", default=_DEFAULT_MODEL_NAME)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)
    parser.add_argument("--model-store-path", default=_DEFAULT_MODEL_STORE_PATH)


def _add_drift_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("drift", help="Compara drift entre versiones")
    parser.add_argument("--from-version", required=True)
    parser.add_argument("--to-version", required=True)
    parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)


def _add_export_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("export", help="Exporta contratos CSV para Power BI")
    export_subparsers = parser.add_subparsers(dest="export_command", required=True)

    features_parser = export_subparsers.add_parser("features", help="Exporta dataset de features")
    features_parser.add_argument("--dataset-version", required=True)
    features_parser.add_argument("--output", required=True)
    features_parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)

    metrics_parser = export_subparsers.add_parser("metrics", help="Exporta métricas del modelo")
    metrics_parser.add_argument("--model-name", default=_DEFAULT_MODEL_NAME)
    metrics_parser.add_argument("--model-version", required=True)
    metrics_parser.add_argument("--dataset-version", required=True)
    metrics_parser.add_argument("--output", required=True)
    metrics_parser.add_argument("--model-store-path", default=_DEFAULT_MODEL_STORE_PATH)

    scoring_parser = export_subparsers.add_parser("scoring", help="Exporta scoring")
    scoring_parser.add_argument("--dataset-version", required=True)
    scoring_parser.add_argument("--predictor", choices=("baseline", "trained"), default="trained")
    scoring_parser.add_argument("--model-version", required=True)
    scoring_parser.add_argument("--output", required=True)
    scoring_parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)
    scoring_parser.add_argument("--model-store-path", default=_DEFAULT_MODEL_STORE_PATH)

    drift_parser = export_subparsers.add_parser("drift", help="Exporta drift entre versiones")
    drift_parser.add_argument("--from-version", required=True)
    drift_parser.add_argument("--to-version", required=True)
    drift_parser.add_argument("--output", required=True)
    drift_parser.add_argument("--feature-store-path", default=_DEFAULT_FEATURE_STORE_PATH)


def _add_seed_demo_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("seed-demo", help="Genera dataset demo reproducible en SQLite")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--doctors", type=int, default=10)
    parser.add_argument("--patients", type=int, default=80)
    parser.add_argument("--appointments", type=int, default=300)
    parser.add_argument("--from", dest="from_date", type=str, default=None)
    parser.add_argument("--to", dest="to_date", type=str, default=None)
    parser.add_argument("--incidence-rate", type=float, default=0.15)
    parser.add_argument("--sqlite-path", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--meds", type=int, default=200)
    parser.add_argument("--materials", type=int, default=120)
    parser.add_argument("--recipes", type=int, default=400)
    parser.add_argument("--movements", type=int, default=2000)
    parser.add_argument("--turns-months", type=int, default=2)
    parser.add_argument("--absences", type=int, default=60)
    parser.add_argument("--turbo", dest="turbo", action="store_true", default=True)
    parser.add_argument("--no-turbo", dest="turbo", action="store_false")
    parser.add_argument("--reset", dest="reset", action="store_true", default=None)
    parser.add_argument("--no-reset", dest="reset", action="store_false")


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging("clinicdesk-ml-cli", Path("./logs"), level="INFO", json=True)
    set_run_context(uuid.uuid4().hex[:8])
    install_global_exception_hook(_LOGGER)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build-features":
            return _handle_build_features(args)
        if args.command == "train":
            return _handle_train(args)
        if args.command == "score":
            return _handle_score(args)
        if args.command == "drift":
            return _handle_drift(args)
        if args.command == "export":
            return _handle_export(args)
        if args.command == "seed-demo":
            return _handle_seed_demo(args)
        parser.error("Comando no soportado")
    except (ValueError, UnsafeDatabaseResetError) as exc:
        log_soft_exception(_LOGGER, exc, {"command": getattr(args, "command", "-")})
        return 2
    return 0


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada invocable desde otros módulos sin subprocess."""
    return main(argv)


def _handle_build_features(args: argparse.Namespace) -> int:
    desde, hasta = _resolve_range(args.from_date, args.to_date)
    read_adapter = _build_read_adapter(args.demo_fake, args.demo_profile, desde, hasta)
    dataset_rows = BuildCitasDataset(read_adapter).execute(desde, hasta)
    features = build_citas_features(dataset_rows)
    quality = compute_citas_quality_report(features)
    store = FeatureStoreService(LocalJsonFeatureStore(args.store_path))
    version = store.save_citas_features_with_artifacts(features, quality, version=args.version)
    _LOGGER.info("saved_version=%s row_count=%s suspicious_count=%s", version, quality.total, quality.suspicious_count)
    return 0


def _build_read_adapter(
    demo_fake: bool,
    demo_profile: str,
    desde: datetime,
    hasta: datetime,
) -> CitasReadPort:
    if demo_fake:
        return FakeCitasReadAdapter(_make_fake_citas(demo_profile, desde, 40))
    try:
        connection = bootstrap_database(apply_schema=True)
        return SqliteCitasReadAdapter(CitasRepository(connection), IncidenciasRepository(connection))
    except sqlite3.Error:
        return FakeCitasReadAdapter(_make_fake_citas(demo_profile, desde, 40))


def _resolve_range(from_date: str | None, to_date: str | None) -> tuple[datetime, datetime]:
    now = datetime.now().replace(microsecond=0)
    default_from = now - timedelta(days=30)
    desde = _parse_date(from_date, default=default_from)
    hasta = _parse_date(to_date, default=now)
    if hasta < desde:
        raise ValueError("Rango inválido: --to no puede ser menor que --from")
    return desde, hasta


def _parse_date(raw: str | None, *, default: datetime) -> datetime:
    if not raw:
        return default
    return datetime.strptime(raw, "%Y-%m-%d")


def _make_fake_citas(profile: str, start: datetime, total: int) -> list[CitaReadModel]:
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


def _handle_train(args: argparse.Namespace) -> int:
    _require_default_model_name(args.model_name)
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    model_store = LocalJsonModelStore(args.model_store_path)
    response = TrainCitasModel(feature_store, model_store).execute(
        TrainCitasModelRequest(dataset_version=args.dataset_version, model_version=args.model_version)
    )
    _LOGGER.info(
        "model="
        f"{response.model_name}@{response.model_version} "
        f"train_precision={response.train_metrics.precision:.3f} "
        f"test_recall={response.test_metrics.recall:.3f} "
        f"calibrated_threshold={response.calibrated_threshold:.3f}"
    )
    return 0


def _handle_score(args: argparse.Namespace) -> int:
    _require_default_model_name(args.model_name)
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    model_store = LocalJsonModelStore(args.model_store_path)
    use_case = ScoreCitas(feature_store, BaselineCitasPredictor(), model_store=model_store)
    response = use_case.execute(
        ScoreCitasRequest(
            dataset_version=args.dataset_version,
            limit=args.limit,
            predictor_kind=args.predictor,
            model_version=args.model_version,
        )
    )
    _print_score_table(response.items, top_n=args.limit or 10)
    labels = Counter(item.label for item in response.items)
    _LOGGER.info("summary_labels=%s total=%s", dict(labels), response.total)
    return 0


def _print_score_table(items: list, top_n: int) -> None:
    _LOGGER.info("cita_id | score | label | reasons")
    for item in items[:top_n]:
        reasons = ",".join(item.reasons[:3])
        _LOGGER.info("%s | %.3f | %s | %s", item.cita_id, item.score, item.label, _truncate(reasons, 64))


def _truncate(value: str, max_len: int) -> str:
    return value if len(value) <= max_len else f"{value[: max_len - 3]}..."


def _handle_drift(args: argparse.Namespace) -> int:
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    report = DriftCitasFeatures(feature_store).execute(
        DriftCitasFeaturesRequest(from_version=args.from_version, to_version=args.to_version)
    )
    psi_fmt = {key: round(value, 4) for key, value in report.psi_by_feature.items()}
    _LOGGER.info("psi_by_feature=%s", psi_fmt)
    _LOGGER.info("overall_flag=%s from=%s to=%s", report.overall_flag, report.from_version, report.to_version)
    return 0


def _require_default_model_name(model_name: str) -> None:
    if model_name != _DEFAULT_MODEL_NAME:
        raise ValueError(f"model-name no soportado todavía: '{model_name}' (use '{_DEFAULT_MODEL_NAME}')")


def _handle_export(args: argparse.Namespace) -> int:
    if args.export_command == "features":
        return _export_features(args)
    if args.export_command == "metrics":
        return _export_metrics(args)
    if args.export_command == "scoring":
        return _export_scoring(args)
    if args.export_command == "drift":
        return _export_drift(args)
    raise ValueError(f"Subcomando export no soportado: {args.export_command}")


def _export_features(args: argparse.Namespace) -> int:
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    rows = feature_store.load_citas_features(args.dataset_version)
    output = ExportFeaturesCSV().execute(args.dataset_version, rows, args.output)
    _LOGGER.info(output)
    return 0


def _export_metrics(args: argparse.Namespace) -> int:
    _require_default_model_name(args.model_name)
    model_store = LocalJsonModelStore(args.model_store_path)
    _, metadata = model_store.load_model(args.model_name, args.model_version)
    metrics = _build_metrics_export_data(args, metadata)
    output = ExportModelMetricsFromMetadataCSV().execute(metrics, args.output)
    _LOGGER.info(output)
    return 0


def _export_scoring(args: argparse.Namespace) -> int:
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    model_store = LocalJsonModelStore(args.model_store_path)
    score_response = ScoreCitas(feature_store, BaselineCitasPredictor(), model_store=model_store).execute(
        ScoreCitasRequest(
            dataset_version=args.dataset_version,
            predictor_kind=args.predictor,
            model_version=args.model_version,
        )
    )
    threshold_used = _resolve_threshold_used(args.predictor, args.model_version, model_store)
    output = ExportScoringCSV().execute(
        score_response,
        predictor_kind=args.predictor,
        model_version=args.model_version,
        threshold_used=threshold_used,
        output_path=args.output,
    )
    _LOGGER.info(output)
    return 0


def _export_drift(args: argparse.Namespace) -> int:
    feature_store = FeatureStoreService(LocalJsonFeatureStore(args.feature_store_path))
    report = DriftCitasFeatures(feature_store).execute(
        DriftCitasFeaturesRequest(from_version=args.from_version, to_version=args.to_version)
    )
    output = ExportDriftCSV().execute(report, args.output)
    _LOGGER.info(output)
    return 0


def _build_metrics_export_data(args: argparse.Namespace, metadata: dict) -> ModelMetricsExportData:
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


def _resolve_threshold_used(predictor_kind: str, model_version: str, model_store: LocalJsonModelStore) -> float:
    if predictor_kind == "baseline":
        return 0.5
    _, metadata = model_store.load_model(_DEFAULT_MODEL_NAME, model_version)
    return float(metadata.get("calibrated_threshold", 0.5))


def _handle_seed_demo(args: argparse.Namespace) -> int:
    target_path = _resolve_sqlite_path(args.sqlite_path)
    should_reset = _resolve_reset_flag(args.reset, target_path)
    if should_reset:
        _LOGGER.info("seed_demo_reset_requested path=%s", target_path)
        reset_demo_database(target_path)
    connection = _open_sqlite_connection(target_path)
    try:
        response = _run_seed_demo_use_case(args, connection)
    finally:
        connection.close()
    _LOGGER.info(
        "seeded "
        f"doctors={response.doctors} patients={response.patients} personal={response.personal} "
        f"appointments={response.appointments} incidences={response.incidences} "
        f"range={response.from_date}:{response.to_date} dataset_version={response.dataset_version}"
    )
    _LOGGER.info("next: build-features --from %s --to %s", response.from_date, response.to_date)
    _LOGGER.info("next: train --dataset-version <version>")
    _LOGGER.info("next: export features --dataset-version <version> --output ./out/features.csv")
    return 0


def _run_seed_demo_use_case(args: argparse.Namespace, connection: sqlite3.Connection):
    request = SeedDemoDataRequest(
        seed=args.seed,
        n_doctors=args.doctors,
        n_patients=args.patients,
        n_appointments=args.appointments,
        from_date=args.from_date,
        to_date=args.to_date,
        incidence_rate=args.incidence_rate,
        batch_size=args.batch_size,
        n_medicamentos=args.meds,
        n_materiales=args.materials,
        n_recetas=args.recipes,
        n_movimientos=args.movements,
        turns_months=args.turns_months,
        n_ausencias=args.absences,
    )
    if not args.turbo:
        _LOGGER.info("seed_demo_turbo_disabled")
        return SeedDemoData(DemoDataSeeder(connection)).execute(request)
    _LOGGER.info("seed_demo_turbo_enabled")
    with sqlite_seed_turbo(connection):
        return SeedDemoData(DemoDataSeeder(connection)).execute(request)


def _resolve_sqlite_path(raw_sqlite_path: str | None) -> Path:
    return resolve_db_path(raw_sqlite_path)


def _resolve_reset_flag(reset_arg: bool | None, sqlite_path: Path) -> bool:
    if reset_arg is not None:
        return reset_arg
    return is_safe_demo_db_path(sqlite_path)


def _open_sqlite_connection(sqlite_path: Path) -> sqlite3.Connection:
    return bootstrap_database(apply_schema=True, sqlite_path=sqlite_path.as_posix())


if __name__ == "__main__":
    raise SystemExit(main())

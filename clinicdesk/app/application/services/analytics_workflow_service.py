from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol, TypedDict

from clinicdesk.app.application.ml.drift_explain import explain_drift
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.services.demo_run_service import CancelToken
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest
from clinicdesk.app.bootstrap_logging import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class AnalyticsWorkflowConfig:
    export_dir: str
    score_limit: int = 20
    drift_enabled: bool = True
    predictor_kind: str = "trained"
    seed_if_missing: bool = False


@dataclass(slots=True, frozen=True)
class AnalyticsWorkflowResult:
    export_paths: dict[str, str]
    metrics: MetricsWorkflow
    drift_flag: bool
    summary_text: str
    internal_versions: VersionesInternasWorkflow


class MetricsWorkflow(TypedDict):
    accuracy: float
    threshold: float
    score_total: float


class VersionesInternasWorkflow(TypedDict):
    dataset_version: str
    model_version: str


class MetricasEntrenamiento(Protocol):
    accuracy: float


class RespuestaEntrenamiento(Protocol):
    model_version: str
    calibrated_threshold: float
    test_metrics: MetricasEntrenamiento


class RespuestaScoring(Protocol):
    total: int


class ReporteDrift(Protocol):
    overall_flag: bool


ProgressCallback = Callable[[int, str], None]


@dataclass(slots=True, frozen=True)
class ContextoWorkflow:
    dataset_version: str
    model_version: str
    train_response: RespuestaEntrenamiento
    score_response: RespuestaScoring
    drift_report: ReporteDrift | None
    drift_flag: bool


class AnalyticsWorkflowService:
    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade

    def prepare_analysis(self, from_date: str, to_date: str, version: str | None = None) -> str:
        return self._facade.build_features(from_date, to_date, version)

    def train(self, dataset_version: str, model_version: str | None = None) -> tuple[RespuestaEntrenamiento, str]:
        response = self._facade.train(dataset_version, model_version)
        return response, response.model_version

    def score(
        self,
        dataset_version: str,
        model_version: str,
        score_limit: int,
        predictor_kind: str = "trained",
    ) -> RespuestaScoring:
        return self._facade.score(
            dataset_version,
            predictor_kind=predictor_kind,
            model_version=model_version,
            limit=score_limit,
        )

    def drift(self, from_version: str, to_version: str) -> ReporteDrift:
        return self._facade.drift(from_version, to_version)

    def export_all(
        self,
        dataset_version: str,
        train_response: RespuestaEntrenamiento,
        score_response: RespuestaScoring,
        drift_report: ReporteDrift | None,
        config: AnalyticsWorkflowConfig,
    ) -> dict[str, str]:
        threshold = train_response.calibrated_threshold
        run_ts = datetime.now(tz=timezone.utc).isoformat()
        paths = {
            "features": self._facade.export_features(dataset_version, config.export_dir),
            "metrics": self._facade.export_metrics(train_response, config.export_dir),
            "scoring": self._facade.export_scoring(
                score_response,
                predictor_kind=config.predictor_kind,
                model_version=train_response.model_version,
                threshold_used=threshold,
                output_path=config.export_dir,
            ),
        }
        if drift_report is not None:
            paths["drift"] = self._facade.export_drift(drift_report, config.export_dir)
        paths.update(
            self._facade.export_kpis(
                dataset_version=dataset_version,
                predictor_kind=config.predictor_kind,
                train_response=train_response,
                score_response=score_response,
                drift_report=drift_report,
                output_path=config.export_dir,
                run_ts=run_ts,
            )
        )
        return paths

    def run_full_workflow(
        self,
        from_date: str,
        to_date: str,
        config: AnalyticsWorkflowConfig,
        previous_dataset_version: str | None = None,
        seed_request: SeedDemoDataRequest | None = None,
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
        progress_cb: ProgressCallback | None = None,
    ) -> AnalyticsWorkflowResult:
        cb = progress_callback or progress_cb
        self._notify(cb, 0, "Iniciando análisis guiado")
        self._check_cancel(cancel_token)
        if seed_request is not None and config.seed_if_missing:
            self._notify(cb, 5, "Generando datos demo")
            self._facade.seed_demo(seed_request)
        contexto = self._ejecutar_pipeline(
            from_date=from_date,
            to_date=to_date,
            config=config,
            previous_dataset_version=previous_dataset_version,
            cancel_token=cancel_token,
            progress_cb=cb,
        )
        self._notify(cb, 90, "Exportando resultados")
        exports = self.export_all(
            contexto.dataset_version,
            contexto.train_response,
            contexto.score_response,
            contexto.drift_report,
            config,
        )
        summary = self._build_summary(contexto.score_response.total, exports, contexto.drift_flag)
        metrics = self._build_metrics(contexto.train_response, contexto.score_response)
        self._notify(cb, 100, "Análisis completo")
        result = AnalyticsWorkflowResult(
            export_paths=exports,
            metrics=metrics,
            drift_flag=contexto.drift_flag,
            summary_text=summary,
            internal_versions={
                "dataset_version": contexto.dataset_version,
                "model_version": contexto.model_version,
            },
        )
        LOGGER.info("analytics_workflow_completed", extra={"exports": len(exports), "drift": contexto.drift_flag})
        return result

    def _ejecutar_pipeline(
        self,
        *,
        from_date: str,
        to_date: str,
        config: AnalyticsWorkflowConfig,
        previous_dataset_version: str | None,
        cancel_token: CancelToken | None,
        progress_cb: ProgressCallback | None,
    ) -> ContextoWorkflow:
        dataset_version = self._build_dataset_version()
        model_version = self._build_model_version()
        self._notify(progress_cb, 15, "Preparando análisis")
        dataset_version = self.prepare_analysis(from_date, to_date, dataset_version)
        self._check_cancel(cancel_token)
        self._notify(progress_cb, 40, "Entrenando")
        train_response, model_version = self.train(dataset_version, model_version)
        self._check_cancel(cancel_token)
        self._notify(progress_cb, 60, "Calculando riesgo")
        score_response = self.score(dataset_version, model_version, config.score_limit, config.predictor_kind)
        self._check_cancel(cancel_token)
        drift_report, drift_flag = self._resolver_drift(
            config=config,
            previous_dataset_version=previous_dataset_version,
            dataset_version=dataset_version,
            progress_cb=progress_cb,
        )
        self._check_cancel(cancel_token)
        return ContextoWorkflow(
            dataset_version=dataset_version,
            model_version=model_version,
            train_response=train_response,
            score_response=score_response,
            drift_report=drift_report,
            drift_flag=drift_flag,
        )

    def _resolver_drift(
        self,
        *,
        config: AnalyticsWorkflowConfig,
        previous_dataset_version: str | None,
        dataset_version: str,
        progress_cb: ProgressCallback | None,
    ) -> tuple[ReporteDrift | None, bool]:
        if not config.drift_enabled:
            return None, False
        self._notify(progress_cb, 78, "Detectando cambios")
        source_version = previous_dataset_version or dataset_version
        drift_report = self.drift(source_version, dataset_version)
        return drift_report, bool(drift_report.overall_flag)

    def _build_metrics(
        self,
        train_response: RespuestaEntrenamiento,
        score_response: RespuestaScoring,
    ) -> MetricsWorkflow:
        return {
            "accuracy": float(train_response.test_metrics.accuracy),
            "threshold": float(train_response.calibrated_threshold),
            "score_total": float(score_response.total),
        }

    def _notify(self, progress_cb: ProgressCallback | None, progress: int, message: str) -> None:
        if progress_cb is not None:
            progress_cb(progress, message)

    def _check_cancel(self, cancel_token: CancelToken | None) -> None:
        if cancel_token is not None and cancel_token.is_cancelled():
            LOGGER.info("analytics_workflow_cancelled")
            raise RuntimeError("Operación cancelada por la persona usuaria")

    def _build_dataset_version(self) -> str:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"analytics_{stamp}"

    def _build_model_version(self) -> str:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"model_{stamp}"

    def _build_summary(self, scored: int, exports: dict[str, str], drift_flag: bool) -> str:
        drift_text = "Se detectaron cambios" if drift_flag else "Sin cambios relevantes"
        return f"Se analizaron {scored} citas. {drift_text}. Archivos exportados: {len(exports)}"

    def summarize_drift(self, drift_report: ReporteDrift | None) -> tuple[str, float]:
        if drift_report is None:
            return "GREEN", 0.0
        severity, _, psi_max = explain_drift(drift_report)
        return severity.value, psi_max

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

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
    metrics: dict[str, float]
    drift_flag: bool
    summary_text: str
    internal_versions: dict[str, str]


class AnalyticsWorkflowService:
    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade

    def prepare_analysis(self, from_date: str, to_date: str, version: str | None = None) -> str:
        return self._facade.build_features(from_date, to_date, version)

    def train(self, dataset_version: str, model_version: str | None = None) -> tuple[Any, str]:
        response = self._facade.train(dataset_version, model_version)
        return response, response.model_version

    def score(self, dataset_version: str, model_version: str, score_limit: int, predictor_kind: str = "trained") -> Any:
        return self._facade.score(
            dataset_version,
            predictor_kind=predictor_kind,
            model_version=model_version,
            limit=score_limit,
        )

    def drift(self, from_version: str, to_version: str) -> Any:
        return self._facade.drift(from_version, to_version)

    def export_all(
        self,
        dataset_version: str,
        train_response: Any,
        score_response: Any,
        drift_report: Any | None,
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
        progress_cb: Callable[[int, str, str], None] | None = None,
    ) -> AnalyticsWorkflowResult:
        dataset_version = self._build_dataset_version()
        model_version = self._build_model_version()
        self._notify(progress_cb, 0, "running", "Iniciando análisis guiado")
        self._check_cancel(cancel_token)
        if seed_request is not None and config.seed_if_missing:
            self._notify(progress_cb, 5, "running", "Generando datos demo")
            self._facade.seed_demo(seed_request)
        self._notify(progress_cb, 15, "running", "Preparando análisis")
        dataset_version = self.prepare_analysis(from_date, to_date, dataset_version)
        self._check_cancel(cancel_token)
        self._notify(progress_cb, 40, "running", "Entrenando")
        train_response, model_version = self.train(dataset_version, model_version)
        self._check_cancel(cancel_token)
        self._notify(progress_cb, 60, "running", "Calculando riesgo")
        score_response = self.score(dataset_version, model_version, config.score_limit, config.predictor_kind)
        self._check_cancel(cancel_token)
        drift_report = None
        drift_flag = False
        if config.drift_enabled:
            self._notify(progress_cb, 78, "running", "Detectando cambios")
            source_version = previous_dataset_version or dataset_version
            drift_report = self.drift(source_version, dataset_version)
            drift_flag = bool(getattr(drift_report, "overall_flag", False))
        self._check_cancel(cancel_token)
        self._notify(progress_cb, 90, "running", "Exportando resultados")
        exports = self.export_all(dataset_version, train_response, score_response, drift_report, config)
        summary = self._build_summary(score_response.total, exports, drift_flag)
        metrics = {
            "accuracy": float(getattr(train_response.test_metrics, "accuracy", 0.0)),
            "threshold": float(train_response.calibrated_threshold),
            "score_total": float(score_response.total),
        }
        self._notify(progress_cb, 100, "done", "Análisis completo")
        result = AnalyticsWorkflowResult(
            export_paths=exports,
            metrics=metrics,
            drift_flag=drift_flag,
            summary_text=summary,
            internal_versions={"dataset_version": dataset_version, "model_version": model_version},
        )
        LOGGER.info("analytics_workflow_completed", extra={"exports": len(exports), "drift": drift_flag})
        return result

    def _notify(self, progress_cb: Callable[[int, str, str], None] | None, progress: int, status: str, message: str) -> None:
        if progress_cb is not None:
            progress_cb(progress, status, message)

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

    def summarize_drift(self, drift_report: Any | None) -> tuple[str, float]:
        if drift_report is None:
            return "GREEN", 0.0
        severity, _, psi_max = explain_drift(drift_report)
        return severity.value, psi_max

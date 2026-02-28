from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from clinicdesk.app.application.services.analytics_workflow_service import (
    AnalyticsWorkflowConfig,
    AnalyticsWorkflowService,
)
from clinicdesk.app.application.services.demo_run_service import CancelToken
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest


@dataclass(slots=True)
class _FakeScoreItem:
    cita_id: str
    score: float
    label: str
    reasons: list[str]


class FakeDemoMLFacade:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def seed_demo(self, req):
        self.calls.append("seed")
        return SimpleNamespace(dataset_version="seed_v1", appointments=req.n_appointments)

    def build_features(self, from_date: str, to_date: str, version: str | None = None) -> str:
        self.calls.append("build")
        return version or "analytics_v1"

    def train(self, dataset_version: str, model_version: str | None = None):
        self.calls.append("train")
        return SimpleNamespace(
            model_version=model_version or "model_v1",
            calibrated_threshold=0.57,
            test_metrics=SimpleNamespace(accuracy=0.81),
        )

    def score(self, dataset_version: str, predictor_kind: str, model_version: str | None, limit: int | None = None):
        self.calls.append("score")
        item = _FakeScoreItem(cita_id="c_1", score=0.9, label="alto", reasons=["r1"])
        return SimpleNamespace(version=dataset_version, total=limit or 1, items=[item])

    def drift(self, from_version: str, to_version: str):
        self.calls.append("drift")
        return SimpleNamespace(from_version=from_version, to_version=to_version, overall_flag=True, psi_by_feature={"x": 0.3})

    def export_features(self, dataset_version: str, output_path: str) -> str:
        self.calls.append("export_features")
        return f"{output_path}/features.csv"

    def export_metrics(self, train_response, output_path: str) -> str:
        self.calls.append("export_metrics")
        return f"{output_path}/metrics.csv"

    def export_scoring(self, score_response, predictor_kind: str, model_version: str, threshold_used: float, output_path: str) -> str:
        self.calls.append("export_scoring")
        return f"{output_path}/scoring.csv"

    def export_drift(self, report, output_path: str) -> str:
        self.calls.append("export_drift")
        return f"{output_path}/drift.csv"

    def export_kpis(self, dataset_version: str, predictor_kind: str, train_response, score_response, drift_report, output_path: str, run_ts: str | None = None) -> dict[str, str]:
        self.calls.append("export_kpis")
        return {
            "kpi_overview": f"{output_path}/kpi_overview.csv",
            "kpi_scores_by_bucket": f"{output_path}/kpi_scores_by_bucket.csv",
            "kpi_drift_by_feature": f"{output_path}/kpi_drift_by_feature.csv",
            "kpi_training_metrics": f"{output_path}/kpi_training_metrics.csv",
        }


def _seed_request() -> SeedDemoDataRequest:
    return SeedDemoDataRequest(
        seed=123,
        n_doctors=10,
        n_patients=80,
        n_appointments=120,
        from_date="2026-01-01",
        to_date="2026-02-01",
        incidence_rate=0.15,
    )


def test_run_full_workflow_returns_exports_and_summary() -> None:
    facade = FakeDemoMLFacade()
    service = AnalyticsWorkflowService(facade)
    result = service.run_full_workflow(
        "2026-01-01",
        "2026-02-01",
        AnalyticsWorkflowConfig(export_dir="./exports", score_limit=10, drift_enabled=True, seed_if_missing=True),
        previous_dataset_version="prev_v1",
        seed_request=_seed_request(),
    )
    assert "features" in result.export_paths
    assert "scoring" in result.export_paths
    assert "Se analizaron" in result.summary_text
    assert result.drift_flag is True


def test_cancel_token_interrupts_workflow() -> None:
    facade = FakeDemoMLFacade()
    service = AnalyticsWorkflowService(facade)
    token = CancelToken()

    def _progress(pct: int, _status: str, _message: str) -> None:
        if pct >= 40:
            token.cancel()

    with pytest.raises(RuntimeError, match="cancelada"):
        service.run_full_workflow(
            "2026-01-01",
            "2026-02-01",
            AnalyticsWorkflowConfig(export_dir="./exports", score_limit=10, drift_enabled=True),
            cancel_token=token,
            progress_cb=_progress,
        )


def test_drift_is_optional() -> None:
    facade = FakeDemoMLFacade()
    service = AnalyticsWorkflowService(facade)
    result = service.run_full_workflow(
        "2026-01-01",
        "2026-02-01",
        AnalyticsWorkflowConfig(export_dir="./exports", score_limit=5, drift_enabled=False),
    )
    assert "drift" not in result.export_paths
    assert "drift" not in facade.calls

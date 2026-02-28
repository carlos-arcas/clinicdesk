from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from clinicdesk.app.application.services.demo_run_service import (
    CancelToken,
    DemoRunConfig,
    DemoRunService,
)


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
        return version or "demo_ui_x"

    def train(self, dataset_version: str, model_version: str | None = None):
        self.calls.append("train")
        return SimpleNamespace(model_version=model_version or "m_demo_ui_x", calibrated_threshold=0.61)

    def score(self, dataset_version: str, predictor_kind: str = "baseline", model_version: str | None = None, limit: int | None = None):
        self.calls.append("score")
        item = _FakeScoreItem(cita_id="c_1", score=0.9, label="risk", reasons=["r1"])
        return SimpleNamespace(version=dataset_version, total=limit or 1, items=[item])

    def drift(self, from_version: str, to_version: str):
        self.calls.append("drift")
        return SimpleNamespace(from_version=from_version, to_version=to_version, overall_flag="ok", psi_by_feature={"x": 0.1})

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


def _cfg() -> DemoRunConfig:
    return DemoRunConfig(
        seed=123,
        n_doctors=10,
        n_patients=80,
        n_appointments=300,
        from_date="2026-01-01",
        to_date="2026-02-01",
        incidence_rate=0.15,
        export_dir="./exports",
        feature_store_path="./data/feature_store",
        model_store_path="./data/model_store",
        score_limit=20,
        prev_dataset_version="prev_v0",
    )


def test_run_full_demo_executes_expected_order() -> None:
    facade = FakeDemoMLFacade()
    service = DemoRunService(facade)

    result = service.run_full_demo(_cfg())

    assert result.ok is True
    assert [s.step_name for s in result.steps] == ["seed_demo", "build_features", "train", "score", "drift", "export"]
    assert facade.calls == [
        "seed",
        "build",
        "train",
        "score",
        "drift",
        "export_features",
        "export_metrics",
        "export_scoring",
        "export_drift",
    ]


def test_progress_callback_is_monotonic() -> None:
    facade = FakeDemoMLFacade()
    service = DemoRunService(facade)
    progress: list[int] = []

    service.run_full_demo(_cfg(), progress_cb=lambda pct, msg: progress.append(pct))

    assert progress[0] == 0
    assert progress[-1] == 100
    assert progress == sorted(progress)


def test_cancel_stops_flow_before_finish() -> None:
    facade = FakeDemoMLFacade()
    service = DemoRunService(facade)
    token = CancelToken()

    def _progress(pct: int, _: str) -> None:
        if pct >= 30:
            token.cancel()

    result = service.run_full_demo(_cfg(), progress_cb=_progress, cancel_token=token)

    assert result.ok is False
    assert result.steps[-1].message == "Cancelled"
    assert "export_features" not in facade.calls


def test_cli_commands_are_coherent() -> None:
    facade = FakeDemoMLFacade()
    service = DemoRunService(facade)

    result = service.run_full_demo(_cfg())

    assert any("seed-demo" in command for command in result.cli_commands)
    assert any(f"--dataset-version {result.dataset_version}" in command for command in result.cli_commands)
    assert any(f"--model-version {result.model_version}" in command for command in result.cli_commands)


def test_export_paths_include_power_bi_csvs() -> None:
    facade = FakeDemoMLFacade()
    service = DemoRunService(facade)

    result = service.run_full_demo(_cfg())

    assert set(result.export_paths.keys()) == {"features", "metrics", "scoring", "drift"}
    assert all(path.endswith(".csv") for path in result.export_paths.values())

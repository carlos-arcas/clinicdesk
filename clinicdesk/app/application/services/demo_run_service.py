from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Event
from typing import Any, Callable

from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest


@dataclass(slots=True, frozen=True)
class DemoRunConfig:
    seed: int
    n_doctors: int
    n_patients: int
    n_appointments: int
    from_date: str
    to_date: str
    incidence_rate: float
    export_dir: str
    feature_store_path: str
    model_store_path: str
    score_limit: int
    prev_dataset_version: str | None = None


@dataclass(slots=True, frozen=True)
class DemoRunStepResult:
    step_name: str
    ok: bool
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class DemoRunResult:
    ok: bool
    dataset_version: str
    model_version: str
    export_paths: dict[str, str]
    steps: list[DemoRunStepResult]
    cli_commands: list[str]


class CancelToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()


class DemoRunService:
    def __init__(self, facade: DemoMLFacade) -> None:
        self._facade = facade

    def run_full_demo(
        self,
        cfg: DemoRunConfig,
        progress_cb: Callable[[int, str], None] | None = None,
        cancel_token: CancelToken | None = None,
    ) -> DemoRunResult:
        state = self._initial_state(cfg)
        state["cfg"] = cfg
        steps: list[DemoRunStepResult] = []
        self._notify(progress_cb, 0, "Iniciando demo full run")
        plan = self._plan(cfg, state)
        for idx, (pct, name, action) in enumerate(plan, start=1):
            cancelled = self._cancelled_result(cancel_token, steps, state)
            if cancelled is not None:
                return cancelled
            self._notify(progress_cb, pct, f"Paso {idx}/6: {name}")
            cancelled = self._cancelled_result(cancel_token, steps, state)
            if cancelled is not None:
                return cancelled
            step = self._execute_step(name, action)
            steps.append(step)
            if not step.ok:
                return self._result(False, steps, state, {})
        self._notify(progress_cb, 100, "Paso 6/6: export completado")
        return self._result(True, steps, state, state["export_paths"])

    def _plan(self, cfg: DemoRunConfig, state: dict[str, Any]) -> list[tuple[int, str, Callable[[], DemoRunStepResult]]]:
        return [
            (12, "seed_demo", lambda: self._step_seed(cfg)),
            (30, "build_features", lambda: self._step_build_features(cfg, state)),
            (48, "train", lambda: self._step_train(state)),
            (65, "score", lambda: self._step_score(cfg, state)),
            (80, "drift", lambda: self._step_drift(cfg, state)),
            (92, "export", lambda: self._step_export(cfg, state)),
        ]

    def _step_seed(self, cfg: DemoRunConfig) -> DemoRunStepResult:
        req = SeedDemoDataRequest(
            seed=cfg.seed,
            n_doctors=cfg.n_doctors,
            n_patients=cfg.n_patients,
            n_appointments=cfg.n_appointments,
            from_date=cfg.from_date,
            to_date=cfg.to_date,
            incidence_rate=cfg.incidence_rate,
        )
        response = self._facade.seed_demo(req)
        return DemoRunStepResult(
            step_name="seed_demo",
            ok=True,
            message=f"Seed generado: citas={response.appointments}",
            payload={"seed_dataset_version": response.dataset_version},
        )

    def _step_build_features(self, cfg: DemoRunConfig, state: dict[str, Any]) -> DemoRunStepResult:
        dataset_version = self._facade.build_features(cfg.from_date, cfg.to_date, version=state["dataset_version"])
        state["dataset_version"] = dataset_version
        return DemoRunStepResult(
            step_name="build_features",
            ok=True,
            message=f"Features version={dataset_version}",
            payload={"dataset_version": dataset_version},
        )

    def _step_train(self, state: dict[str, Any]) -> DemoRunStepResult:
        response = self._facade.train(state["dataset_version"], model_version=state["model_version"])
        state["model_version"] = response.model_version
        state["train_response"] = response
        return DemoRunStepResult("train", True, f"Modelo version={response.model_version}", {"model_version": response.model_version})

    def _step_score(self, cfg: DemoRunConfig, state: dict[str, Any]) -> DemoRunStepResult:
        response = self._facade.score(
            state["dataset_version"],
            predictor_kind="trained",
            model_version=state["model_version"],
            limit=cfg.score_limit,
        )
        state["score_response"] = response
        return DemoRunStepResult("score", True, f"Scoring total={response.total}", {"total": response.total})

    def _step_drift(self, cfg: DemoRunConfig, state: dict[str, Any]) -> DemoRunStepResult:
        from_version = cfg.prev_dataset_version or state["dataset_version"]
        report = self._facade.drift(from_version, state["dataset_version"])
        state["drift_from"] = from_version
        state["drift_report"] = report
        return DemoRunStepResult("drift", True, f"Drift overall={report.overall_flag}", {"from": from_version})

    def _step_export(self, cfg: DemoRunConfig, state: dict[str, Any]) -> DemoRunStepResult:
        export_dir = cfg.export_dir or "./exports"
        threshold = state["train_response"].calibrated_threshold
        export_paths = {
            "features": self._facade.export_features(state["dataset_version"], export_dir),
            "metrics": self._facade.export_metrics(state["train_response"], export_dir),
            "scoring": self._facade.export_scoring(
                state["score_response"],
                predictor_kind="trained",
                model_version=state["model_version"],
                threshold_used=threshold,
                output_path=export_dir,
            ),
            "drift": self._facade.export_drift(state["drift_report"], export_dir),
        }
        state["export_paths"] = export_paths
        return DemoRunStepResult("export", True, f"Exports en {export_dir}", {"export_paths": export_paths})

    def _execute_step(self, name: str, action: Callable[[], DemoRunStepResult]) -> DemoRunStepResult:
        try:
            return action()
        except Exception as exc:  # noqa: BLE001
            return DemoRunStepResult(step_name=name, ok=False, message=str(exc), payload={})

    def _initial_state(self, cfg: DemoRunConfig) -> dict[str, Any]:
        stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
        return {
            "dataset_version": f"demo_ui_{stamp}",
            "model_version": f"m_demo_ui_{stamp}",
            "drift_from": cfg.prev_dataset_version or "",
            "export_paths": {},
        }

    def _result(
        self,
        ok: bool,
        steps: list[DemoRunStepResult],
        state: dict[str, Any],
        export_paths: dict[str, str],
    ) -> DemoRunResult:
        commands = self._build_cli_commands(state, export_paths, ok)
        return DemoRunResult(
            ok=ok,
            dataset_version=state["dataset_version"],
            model_version=state["model_version"],
            export_paths=export_paths,
            steps=steps,
            cli_commands=commands,
        )

    def _build_cli_commands(self, state: dict[str, Any], export_paths: dict[str, str], ok: bool) -> list[str]:
        if not ok:
            return []
        cfg = state["cfg"] if "cfg" in state else None
        if cfg is None:
            return []
        base = "PYTHONPATH=. python scripts/ml_cli.py"
        return [
            (
                f"{base} seed-demo --seed {cfg.seed} --doctors {cfg.n_doctors} --patients {cfg.n_patients} "
                f"--appointments {cfg.n_appointments} --from {cfg.from_date} --to {cfg.to_date} "
                f"--incidence-rate {cfg.incidence_rate}"
            ),
            f"{base} build-features --version {state['dataset_version']} --from {cfg.from_date} --to {cfg.to_date} --store-path {cfg.feature_store_path}",
            f"{base} train --dataset-version {state['dataset_version']} --model-version {state['model_version']} --feature-store-path {cfg.feature_store_path} --model-store-path {cfg.model_store_path}",
            f"{base} score --dataset-version {state['dataset_version']} --predictor trained --model-version {state['model_version']} --feature-store-path {cfg.feature_store_path} --model-store-path {cfg.model_store_path} --limit {cfg.score_limit}",
            f"{base} drift --from-version {state['drift_from'] or state['dataset_version']} --to-version {state['dataset_version']} --feature-store-path {cfg.feature_store_path}",
            f"{base} export features --dataset-version {state['dataset_version']} --output {cfg.export_dir} --feature-store-path {cfg.feature_store_path}",
            f"{base} export metrics --model-name citas_nb_v1 --model-version {state['model_version']} --dataset-version {state['dataset_version']} --output {cfg.export_dir} --model-store-path {cfg.model_store_path}",
            f"{base} export scoring --dataset-version {state['dataset_version']} --predictor trained --model-version {state['model_version']} --output {cfg.export_dir} --feature-store-path {cfg.feature_store_path} --model-store-path {cfg.model_store_path}",
            f"{base} export drift --from-version {state['drift_from'] or state['dataset_version']} --to-version {state['dataset_version']} --output {cfg.export_dir} --feature-store-path {cfg.feature_store_path}",
        ]

    def _cancelled_result(
        self,
        cancel_token: CancelToken | None,
        steps: list[DemoRunStepResult],
        state: dict[str, Any],
    ) -> DemoRunResult | None:
        if not (cancel_token and cancel_token.is_cancelled()):
            return None
        cancel_step = DemoRunStepResult("cancel", False, "Cancelled", {})
        return DemoRunResult(
            ok=False,
            dataset_version=state["dataset_version"],
            model_version=state["model_version"],
            export_paths={},
            steps=[*steps, cancel_step],
            cli_commands=[],
        )

    def _notify(self, progress_cb: Callable[[int, str], None] | None, pct: int, msg: str) -> None:
        if progress_cb is not None:
            progress_cb(pct, msg)

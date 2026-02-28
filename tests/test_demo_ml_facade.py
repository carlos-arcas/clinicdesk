from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.ml.evaluation import EvalMetrics
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade
from clinicdesk.app.application.usecases.score_citas import ScoreCitasResponse, ScoredCita
from clinicdesk.app.application.usecases.seed_demo_data import SeedDemoDataRequest, SeedDemoDataResponse
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModelResponse


class FakeGateway:
    def list_doctors(self, query, limit):
        return []

    def list_patients(self, query, limit):
        return []

    def list_appointments(self, query, from_date, to_date, limit):
        return []

    def list_incidences(self, query, limit):
        return []


class FakeSeedUC:
    def __init__(self):
        self.called_with = None

    def execute(self, request: SeedDemoDataRequest) -> SeedDemoDataResponse:
        self.called_with = request
        return SeedDemoDataResponse(
            doctors=1,
            patients=2,
            personal=3,
            appointments=4,
            incidences=5,
            medicamentos=6,
            materiales=7,
            recetas=8,
            receta_lineas=9,
            dispensaciones=10,
            movimientos_medicamentos=11,
            movimientos_materiales=12,
            turnos=2,
            ausencias=13,
            from_date="2026-01-01",
            to_date="2026-01-31",
            dataset_version="v_demo",
        )


class FakeScoreUC:
    @dataclass(slots=True)
    class _Req:
        dataset_version: str

    def execute(self, request):
        return ScoreCitasResponse(
            version=request.dataset_version,
            total=1,
            items=[ScoredCita(cita_id="c-1", score=0.7, label="risk", reasons=["ok"])],
        )


class FakeFeatureStoreService:
    def load_citas_features(self, version: str):
        return [{"cita_id": "1", "duracion_min": 30, "duracion_bucket": "30-45", "hora_inicio": 9, "dia_semana": 1, "is_weekend": False, "notas_len": 10, "notas_len_bucket": "short", "has_incidencias": False, "estado_norm": "programada", "is_suspicious": False}]


class FakeBuildDataset:
    def execute(self, desde, hasta):
        return []


class FakeTrainUC:
    def execute(self, request):
        empty = EvalMetrics(accuracy=0, precision=0, recall=0, tp=0, fp=0, tn=0, fn=0)
        return TrainCitasModelResponse(
            model_name="citas_nb_v1",
            model_version=request.model_version or "m1",
            dataset_version=request.dataset_version,
            train_metrics=empty,
            test_metrics=empty,
            calibrated_threshold=0.5,
            test_metrics_at_calibrated_threshold=empty,
        )


class FakeDriftUC:
    def execute(self, request):
        raise AssertionError("no se usa en este test")


def _build_facade(seed_uc=None, score_uc=None):
    return DemoMLFacade(
        read_gateway=FakeGateway(),
        seed_demo_uc=seed_uc or FakeSeedUC(),
        build_dataset=FakeBuildDataset(),
        feature_store_service=FakeFeatureStoreService(),
        train_uc=FakeTrainUC(),
        score_uc=score_uc or FakeScoreUC(),
        drift_uc=FakeDriftUC(),
    )


def test_seed_demo_llama_use_case_y_devuelve_response() -> None:
    seed_uc = FakeSeedUC()
    facade = _build_facade(seed_uc=seed_uc)

    response = facade.seed_demo(SeedDemoDataRequest(seed=77))

    assert seed_uc.called_with is not None
    assert seed_uc.called_with.seed == 77
    assert response.dataset_version == "v_demo"


def test_score_devuelve_datos_para_ui_sin_infra() -> None:
    facade = _build_facade(score_uc=FakeScoreUC())

    response = facade.score("v_demo", predictor_kind="baseline", limit=10)

    assert response.version == "v_demo"
    assert response.total == 1
    assert response.items[0].label == "risk"


def test_export_features_devuelve_path_esperado(tmp_path) -> None:
    facade = _build_facade()

    output = facade.export_features("v_demo", tmp_path)

    assert output.endswith("features_export.csv")

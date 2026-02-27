from __future__ import annotations

from dataclasses import asdict

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModel, TrainCitasModelRequest
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import LocalJsonFeatureStore
from clinicdesk.app.infrastructure.model_store.local_json_model_store import LocalJsonModelStore


def _quality(total: int) -> CitasFeatureQualityReport:
    return CitasFeatureQualityReport(
        total=total,
        suspicious_count=2,
        missing_count=0,
        by_estado={"programada": total},
        by_duracion_bucket={"11-20": total},
        by_notas_bucket={"1-20": total},
    )


def _rows() -> list[CitasFeatureRow]:
    base = [
        CitasFeatureRow("c1", 20, "11-20", 9, 1, False, 12, "1-20", True, "programada", False),
        CitasFeatureRow("c2", 30, "21-40", 10, 2, False, 40, "21-100", False, "programada", True),
        CitasFeatureRow("c3", 10, "0-10", 11, 3, False, 0, "0", False, "realizada", False),
        CitasFeatureRow("c4", 45, "41+", 12, 4, False, 120, "101+", True, "no_show", True),
        CitasFeatureRow("c5", 12, "11-20", 13, 5, True, 8, "1-20", False, "programada", False),
        CitasFeatureRow("c6", 35, "21-40", 14, 6, True, 35, "21-100", False, "programada", False),
    ]
    return base


def test_train_usecase_trains_evaluates_and_registers_model(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "registry")

    version = feature_service.save_citas_features_with_artifacts(_rows(), _quality(6), version="dataset-v1")
    response = TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=version, model_version="model-v1")
    )

    assert response.model_name == "citas_nb_v1"
    assert response.model_version == "model-v1"
    assert 0.0 <= response.metrics.accuracy <= 1.0
    assert 0.0 <= response.metrics.precision <= 1.0
    assert 0.0 <= response.metrics.recall <= 1.0

    payload, metadata = model_store.load_model("citas_nb_v1", "model-v1")
    assert payload["model_name"] == "citas_nb_v1"
    assert metadata["trained_on_dataset_version"] == "dataset-v1"
    assert metadata["metrics"]["accuracy"] == asdict(response.metrics)["accuracy"]

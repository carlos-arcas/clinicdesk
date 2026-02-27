from __future__ import annotations

import json

import pytest

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.score_citas import ScoreCitas, ScoreCitasRequest, ScoringValidationError
from clinicdesk.app.application.usecases.train_citas_model import TrainCitasModel, TrainCitasModelRequest
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import LocalJsonFeatureStore
from clinicdesk.app.infrastructure.model_store.local_json_model_store import LocalJsonModelStore


def _quality(total: int) -> CitasFeatureQualityReport:
    return CitasFeatureQualityReport(
        total=total,
        suspicious_count=0,
        missing_count=0,
        by_estado={"programada": total},
        by_duracion_bucket={"21-40": total},
        by_notas_bucket={"1-20": total},
    )


def _rows() -> list[CitasFeatureRow]:
    return [
        CitasFeatureRow("r1", 20, "11-20", 8, 1, False, 4, "1-20", True, "programada", False),
        CitasFeatureRow("r2", 30, "21-40", 10, 2, False, 22, "21-100", False, "programada", True),
        CitasFeatureRow("r3", 30, "21-40", 12, 3, False, 9, "1-20", False, "realizada", False),
    ]


def test_score_citas_with_trained_predictor_is_deterministic(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "models")
    dataset_version = feature_service.save_citas_features_with_artifacts(_rows(), _quality(3), version="dsv1")
    TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=dataset_version, model_version="m1")
    )

    usecase = ScoreCitas(feature_service, BaselineCitasPredictor(), model_store=model_store)
    request = ScoreCitasRequest(dataset_version=dataset_version, predictor_kind="trained", model_version="m1")

    first = usecase.execute(request)
    second = usecase.execute(request)

    assert [item.score for item in first.items] == [item.score for item in second.items]
    assert all("trained_model:citas_nb_v1@m1" in item.reasons for item in first.items)


def test_score_citas_trained_raises_for_schema_mismatch(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "models")
    dataset_version = feature_service.save_citas_features_with_artifacts(_rows(), _quality(3), version="dsv1")
    TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=dataset_version, model_version="m1")
    )

    metadata_path = tmp_path / "models" / "models" / "citas_nb_v1" / "m1.metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["schema_hash"] = "broken"
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    usecase = ScoreCitas(feature_service, BaselineCitasPredictor(), model_store=model_store)
    with pytest.raises(ScoringValidationError, match="schema_hash mismatch"):
        usecase.execute(
            ScoreCitasRequest(dataset_version=dataset_version, predictor_kind="trained", model_version="m1")
        )

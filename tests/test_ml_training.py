from __future__ import annotations

from dataclasses import asdict

import pytest

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.train_citas_model import (
    TrainCitasModel,
    TrainCitasModelNotEnoughDataError,
    TrainCitasModelRequest,
)
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


def _rows(size: int = 30) -> list[CitasFeatureRow]:
    rows: list[CitasFeatureRow] = []
    for idx in range(size):
        rows.append(
            CitasFeatureRow(
                cita_id=f"c{idx}",
                duracion_min=20 + (idx % 3) * 10,
                duracion_bucket="11-20" if idx % 3 == 0 else "21-40",
                hora_inicio=8 + (idx % 10),
                dia_semana=idx % 7,
                is_weekend=(idx % 7) >= 5,
                notas_len=idx,
                notas_len_bucket="1-20" if idx <= 20 else "21-100",
                has_incidencias=idx % 2 == 0,
                estado_norm="realizada" if idx % 4 == 0 else "programada",
                is_suspicious=idx % 11 == 0,
                inicio_ts=1_700_000_000 + idx,
            )
        )
    return rows


def test_train_usecase_trains_evaluates_and_registers_model(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "registry")

    all_rows = _rows(30)
    version = feature_service.save_citas_features_with_artifacts(all_rows, _quality(len(all_rows)), version="dataset-v1")
    response = TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=version, model_version="model-v1")
    )

    assert response.model_name == "citas_nb_v1"
    assert response.model_version == "model-v1"
    assert 0.0 <= response.train_metrics.accuracy <= 1.0
    assert 0.0 <= response.test_metrics.accuracy <= 1.0

    payload, metadata = model_store.load_model("citas_nb_v1", "model-v1")
    assert payload["model_name"] == "citas_nb_v1"
    assert metadata["trained_on_dataset_version"] == "dataset-v1"
    assert metadata["train_metrics"]["accuracy"] == asdict(response.train_metrics)["accuracy"]
    assert metadata["test_metrics"]["accuracy"] == asdict(response.test_metrics)["accuracy"]
    assert metadata["test_row_count"] == 6
    assert metadata["split_config"] == {"test_ratio": 0.2, "min_train": 20, "time_field": "inicio_ts"}


def test_train_usecase_raises_not_enough_data_for_temporal_holdout(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "registry")

    tiny_rows = _rows(10)
    version = feature_service.save_citas_features_with_artifacts(tiny_rows, _quality(len(tiny_rows)), version="tiny")

    with pytest.raises(TrainCitasModelNotEnoughDataError, match="min_train"):
        TrainCitasModel(feature_service, model_store).execute(TrainCitasModelRequest(dataset_version=version))

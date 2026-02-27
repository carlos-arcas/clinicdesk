from __future__ import annotations

from dataclasses import asdict

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.ports.predictor_port import PredictionResult
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.score_citas import ScoreCitas, ScoreCitasRequest
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


def test_train_citas_model_persists_calibrated_threshold_and_metrics(tmp_path) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "registry")

    version = feature_service.save_citas_features_with_artifacts(_rows(30), _quality(30), version="dataset-v1")
    response = TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=version, model_version="model-v1")
    )

    _, metadata = model_store.load_model("citas_nb_v1", "model-v1")
    assert 0.0 <= response.calibrated_threshold <= 1.0
    assert metadata["calibrated_threshold"] == response.calibrated_threshold
    assert metadata["calibration_policy"] == {"threshold": 0.5, "objective": "min_recall", "value": 0.8}
    assert metadata["test_metrics_at_calibrated_threshold"] == asdict(response.test_metrics_at_calibrated_threshold)


def test_score_citas_trained_uses_calibrated_threshold_from_metadata(tmp_path, monkeypatch) -> None:
    feature_service = FeatureStoreService(LocalJsonFeatureStore(tmp_path / "features"))
    model_store = LocalJsonModelStore(tmp_path / "models")

    version = feature_service.save_citas_features_with_artifacts(_rows(30), _quality(30), version="dataset-v1")
    TrainCitasModel(feature_service, model_store).execute(
        TrainCitasModelRequest(dataset_version=version, model_version="model-v1")
    )

    payload, metadata = model_store.load_model("citas_nb_v1", "model-v1")
    metadata["calibrated_threshold"] = 0.8
    model_store.save_model("citas_nb_v1", "model-v1", payload, metadata)

    import clinicdesk.app.application.usecases.score_citas as score_module

    monkeypatch.setattr(
        score_module,
        "predict_batch_trained",
        lambda model, rows: [PredictionResult(score=0.6, label="high", reasons=["predictor=naive_bayes"]) for _ in rows],
    )

    usecase = ScoreCitas(feature_service, BaselineCitasPredictor(), model_store=model_store)
    response = usecase.execute(
        ScoreCitasRequest(dataset_version=version, predictor_kind="trained", model_version="model-v1", limit=1)
    )

    assert response.items[0].score == 0.6
    assert response.items[0].label == "no_risk"
    assert "threshold:0.80" in response.items[0].reasons

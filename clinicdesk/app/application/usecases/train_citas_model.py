from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.evaluation import EvalMetrics, evaluate
from clinicdesk.app.application.ml.naive_bayes_citas import model_to_dict, train
from clinicdesk.app.application.ml.splitting import (
    TemporalSplitConfig,
    TemporalSplitNotEnoughDataError,
    temporal_train_test_split,
)
from clinicdesk.app.application.ml.targets import derive_target_from_feature
from clinicdesk.app.application.ml_artifacts.feature_artifacts import (
    build_schema_from_dataclass,
    canonical_json_bytes,
    compute_content_hash,
    compute_schema_hash,
)
from clinicdesk.app.application.ports.model_store_port import ModelStorePort
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService


class ModelTrainingValidationError(ValueError):
    """Error explícito de validación durante entrenamiento."""


class TrainCitasModelNotEnoughDataError(ModelTrainingValidationError):
    """Error explícito cuando no hay suficientes datos para split temporal."""


@dataclass(slots=True)
class TrainCitasModelRequest:
    dataset_version: str
    model_version: str | None = None


@dataclass(slots=True)
class TrainCitasModelResponse:
    model_name: str
    model_version: str
    dataset_version: str
    train_metrics: EvalMetrics
    test_metrics: EvalMetrics


class TrainCitasModel:
    MODEL_NAME = "citas_nb_v1"

    def __init__(self, feature_store_service: FeatureStoreService, model_store: ModelStorePort) -> None:
        self._feature_store_service = feature_store_service
        self._model_store = model_store

    def execute(self, request: TrainCitasModelRequest) -> TrainCitasModelResponse:
        if not request.dataset_version.strip():
            raise ModelTrainingValidationError("dataset_version es requerido para entrenar.")
        rows = [_to_feature_row(item) for item in self._feature_store_service.load_citas_features(request.dataset_version)]
        metadata = self._feature_store_service.load_citas_features_metadata(request.dataset_version)
        expected_schema_hash = compute_schema_hash(
            build_schema_from_dataclass(CitasFeatureRow, version=FeatureStoreService.CITAS_SCHEMA_VERSION)
        )
        if metadata.schema_hash != expected_schema_hash:
            raise ModelTrainingValidationError("schema_hash de features incompatible para entrenamiento.")

        split_cfg = TemporalSplitConfig(test_ratio=0.2, min_train=20, time_field="inicio_ts")
        try:
            train_rows, test_rows = temporal_train_test_split(rows, split_cfg)
        except TemporalSplitNotEnoughDataError as exc:
            raise TrainCitasModelNotEnoughDataError(str(exc)) from exc

        model = train(train_rows)
        train_metrics = evaluate(model, train_rows, derive_target_from_feature)
        test_metrics = evaluate(model, test_rows, derive_target_from_feature)
        model_version = request.model_version or self._build_version()
        payload = model_to_dict(model)
        metadata_payload = self._build_metadata_payload(
            request.dataset_version,
            expected_schema_hash,
            payload,
            split_cfg,
            train_metrics,
            test_metrics,
            len(test_rows),
        )
        self._model_store.save_model(self.MODEL_NAME, model_version, payload, metadata_payload)
        return TrainCitasModelResponse(
            model_name=self.MODEL_NAME,
            model_version=model_version,
            dataset_version=request.dataset_version,
            train_metrics=train_metrics,
            test_metrics=test_metrics,
        )

    def _build_version(self) -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")

    def _build_metadata_payload(
        self,
        dataset_version: str,
        schema_hash: str,
        payload: dict,
        split_cfg: TemporalSplitConfig,
        train_metrics: EvalMetrics,
        test_metrics: EvalMetrics,
        test_row_count: int,
    ) -> dict:
        return {
            "trained_on_dataset_version": dataset_version,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "content_hash": compute_content_hash(canonical_json_bytes(payload)),
            "schema_hash": schema_hash,
            "split_config": asdict(split_cfg),
            "train_metrics": asdict(train_metrics),
            "test_metrics": asdict(test_metrics),
            "test_row_count": test_row_count,
            "evaluation_note": "offline eval with deterministic temporal holdout (proxy label)",
        }


def _to_feature_row(raw: object) -> CitasFeatureRow:
    if isinstance(raw, CitasFeatureRow):
        return raw
    if not isinstance(raw, dict):
        raise ModelTrainingValidationError("Fila de entrenamiento inválida: se esperaba dict o CitasFeatureRow.")
    try:
        return CitasFeatureRow(**raw)
    except TypeError as exc:
        raise ModelTrainingValidationError("Fila de entrenamiento inválida para CitasFeatureRow.") from exc

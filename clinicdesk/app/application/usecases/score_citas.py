from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.naive_bayes_citas import model_from_dict, predict_batch as predict_batch_trained
from clinicdesk.app.application.ml_artifacts.feature_artifacts import canonical_json_bytes, compute_content_hash
from clinicdesk.app.application.ports.model_store_port import ModelStorePort
from clinicdesk.app.application.ports.predictor_port import PredictorPort
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService


class ScoringDatasetNotFoundError(ValueError):
    """Error explícito cuando la versión pedida no existe en el feature store."""


class ScoringValidationError(ValueError):
    """Error explícito de validación para requests/filas de scoring."""


@dataclass(slots=True)
class ScoreCitasRequest:
    dataset_version: str
    limit: int | None = None
    predictor_kind: str = "baseline"
    model_version: str | None = None


@dataclass(slots=True)
class ScoredCita:
    cita_id: str
    score: float
    label: str
    reasons: list[str]


@dataclass(slots=True)
class ScoreCitasResponse:
    version: str
    total: int
    items: list[ScoredCita]


class ScoreCitas:
    TRAINED_MODEL_NAME = "citas_nb_v1"

    def __init__(
        self,
        feature_store_service: FeatureStoreService,
        predictor: PredictorPort,
        model_store: ModelStorePort | None = None,
    ) -> None:
        self._feature_store_service = feature_store_service
        self._predictor = predictor
        self._model_store = model_store

    def execute(self, request: ScoreCitasRequest) -> ScoreCitasResponse:
        self._validate_request(request)
        metadata, metadata_warning = self._load_metadata_if_present(request.dataset_version)
        rows = self._load_rows(request.dataset_version)
        self._validate_rows_against_metadata(request.dataset_version, rows, metadata)
        if request.limit is not None:
            rows = rows[: request.limit]

        features = [_to_feature_row(row) for row in rows]
        predictions, model_reason = self._predict(features, metadata, request)
        scored_items = [
            _to_scored_cita(feature, pred, metadata_warning, model_reason)
            for feature, pred in zip(features, predictions)
        ]

        return ScoreCitasResponse(version=request.dataset_version, total=len(scored_items), items=scored_items)

    def _validate_request(self, request: ScoreCitasRequest) -> None:
        if not request.dataset_version.strip():
            raise ScoringValidationError("dataset_version es requerido.")
        if request.limit is not None and request.limit <= 0:
            raise ScoringValidationError("limit debe ser > 0 cuando se informa.")
        if request.predictor_kind not in {"baseline", "trained"}:
            raise ScoringValidationError("predictor_kind inválido. Use 'baseline' o 'trained'.")
        if request.predictor_kind == "trained" and not (request.model_version or "").strip():
            raise ScoringValidationError("model_version es requerido cuando predictor_kind='trained'.")

    def _load_rows(self, dataset_version: str) -> list[Any]:
        try:
            loaded = self._feature_store_service.load_citas_features(dataset_version)
        except Exception as exc:
            raise ScoringDatasetNotFoundError(
                f"No se pudo cargar dataset de features para versión '{dataset_version}'."
            ) from exc
        if not isinstance(loaded, list):
            raise ScoringValidationError("Payload de feature store inválido: se esperaba list.")
        return loaded

    def _load_metadata_if_present(self, dataset_version: str) -> tuple[Any | None, str | None]:
        try:
            metadata = self._feature_store_service.load_citas_features_metadata(dataset_version)
        except (FileNotFoundError, AttributeError):
            return None, "metadata no disponible para esta versión"
        return metadata, None

    def _validate_rows_against_metadata(
        self, dataset_version: str, rows: list[Any], metadata: Any | None
    ) -> None:
        if metadata is None:
            return
        if metadata.row_count != len(rows):
            raise ScoringValidationError(
                f"Metadata inválida para versión '{dataset_version}': row_count={metadata.row_count} no coincide con {len(rows)} filas."
            )
        actual_hash = compute_content_hash(canonical_json_bytes(rows))
        if metadata.content_hash != actual_hash:
            raise ScoringValidationError(
                f"Metadata inválida para versión '{dataset_version}': content_hash no coincide."
            )

    def _predict(
        self,
        features: list[CitasFeatureRow],
        dataset_metadata: Any | None,
        request: ScoreCitasRequest,
    ) -> tuple[list[Any], str | None]:
        if request.predictor_kind == "baseline":
            return self._predictor.predict_batch(features), None
        model = self._load_trained_model(request.model_version or "")
        self._validate_schema_compatibility(dataset_metadata, model[1])
        predictions = predict_batch_trained(model_from_dict(model[0]), features)
        return predictions, f"trained_model:{self.TRAINED_MODEL_NAME}@{request.model_version}"

    def _load_trained_model(self, model_version: str) -> tuple[dict[str, Any], dict[str, Any]]:
        if self._model_store is None:
            raise ScoringValidationError("Model store no configurado para predictor entrenado.")
        try:
            return self._model_store.load_model(self.TRAINED_MODEL_NAME, model_version)
        except FileNotFoundError as exc:
            raise ScoringValidationError(f"Modelo entrenado no encontrado: versión '{model_version}'.") from exc

    def _validate_schema_compatibility(self, dataset_metadata: Any | None, model_metadata: dict[str, Any]) -> None:
        if dataset_metadata is None:
            return
        if str(model_metadata.get("schema_hash", "")) != str(dataset_metadata.schema_hash):
            raise ScoringValidationError("schema_hash mismatch entre dataset de scoring y modelo entrenado.")


def _to_feature_row(raw: Any) -> CitasFeatureRow:
    if isinstance(raw, CitasFeatureRow):
        return raw
    if not isinstance(raw, dict):
        raise ScoringValidationError("Fila inválida: se esperaba dict o CitasFeatureRow.")
    try:
        return CitasFeatureRow(**raw)
    except TypeError as exc:
        raise ScoringValidationError("Fila de features incompleta o con claves inválidas.") from exc


def _to_scored_cita(
    feature: CitasFeatureRow,
    prediction: Any,
    warning: str | None,
    model_reason: str | None,
) -> ScoredCita:
    reasons = list(prediction.reasons)
    if warning and warning not in reasons:
        reasons.append(warning)
    if model_reason and model_reason not in reasons:
        reasons.append(model_reason)
    return ScoredCita(cita_id=feature.cita_id, score=prediction.score, label=prediction.label, reasons=reasons)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
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
    def __init__(self, feature_store_service: FeatureStoreService, predictor: PredictorPort) -> None:
        self._feature_store_service = feature_store_service
        self._predictor = predictor

    def execute(self, request: ScoreCitasRequest) -> ScoreCitasResponse:
        self._validate_request(request)
        rows = self._load_rows(request.dataset_version)
        if request.limit is not None:
            rows = rows[: request.limit]

        features = [_to_feature_row(row) for row in rows]
        predictions = self._predictor.predict_batch(features)
        scored_items = [_to_scored_cita(feature, pred) for feature, pred in zip(features, predictions)]

        return ScoreCitasResponse(
            version=request.dataset_version,
            total=len(scored_items),
            items=scored_items,
        )

    def _validate_request(self, request: ScoreCitasRequest) -> None:
        if not request.dataset_version.strip():
            raise ScoringValidationError("dataset_version es requerido.")
        if request.limit is not None and request.limit <= 0:
            raise ScoringValidationError("limit debe ser > 0 cuando se informa.")

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


def _to_feature_row(raw: Any) -> CitasFeatureRow:
    if isinstance(raw, CitasFeatureRow):
        return raw
    if not isinstance(raw, dict):
        raise ScoringValidationError("Fila inválida: se esperaba dict o CitasFeatureRow.")
    try:
        return CitasFeatureRow(**raw)
    except TypeError as exc:
        raise ScoringValidationError("Fila de features incompleta o con claves inválidas.") from exc


def _to_scored_cita(feature: CitasFeatureRow, prediction: Any) -> ScoredCita:
    return ScoredCita(
        cita_id=feature.cita_id,
        score=prediction.score,
        label=prediction.label,
        reasons=prediction.reasons,
    )

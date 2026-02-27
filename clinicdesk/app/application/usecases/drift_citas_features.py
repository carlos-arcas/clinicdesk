from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.drift import DriftReport, compute_citas_drift
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService


class DriftCitasFeaturesValidationError(ValueError):
    """Error explícito de validación para drift de features."""


@dataclass(slots=True)
class DriftCitasFeaturesRequest:
    from_version: str
    to_version: str


class DriftCitasFeatures:
    def __init__(self, feature_store_service: FeatureStoreService) -> None:
        self._feature_store_service = feature_store_service

    def execute(self, request: DriftCitasFeaturesRequest) -> DriftReport:
        self._validate_request(request)
        rows_from = self._load_rows(request.from_version)
        rows_to = self._load_rows(request.to_version)
        return compute_citas_drift(rows_from, rows_to, request.from_version, request.to_version)

    def _validate_request(self, request: DriftCitasFeaturesRequest) -> None:
        if not request.from_version.strip() or not request.to_version.strip():
            raise DriftCitasFeaturesValidationError("from_version y to_version son requeridos.")

    def _load_rows(self, version: str) -> list[CitasFeatureRow]:
        loaded = self._feature_store_service.load_citas_features(version)
        return [_to_feature_row(item) for item in loaded]


def _to_feature_row(raw: object) -> CitasFeatureRow:
    if isinstance(raw, CitasFeatureRow):
        return raw
    if not isinstance(raw, dict):
        raise DriftCitasFeaturesValidationError("Fila inválida en drift: se esperaba dict o CitasFeatureRow.")
    try:
        return CitasFeatureRow(**raw)
    except TypeError as exc:
        raise DriftCitasFeaturesValidationError("Fila inválida para drift de CitasFeatureRow.") from exc

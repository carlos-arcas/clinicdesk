from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from clinicdesk.app.application.ports.feature_store_port import FeatureStorePort


class FeatureStoreService:
    """Servicio liviano para gestión del dataset de features de citas."""

    CITAS_DATASET_NAME = "citas_features"

    def __init__(self, feature_store: FeatureStorePort) -> None:
        self._feature_store = feature_store

    def save_citas_features(self, rows: list[Any], version: str | None = None) -> str:
        resolved_version = version or self._build_version()
        serialized_rows = [_to_serializable(row) for row in rows]
        self._feature_store.save(self.CITAS_DATASET_NAME, resolved_version, serialized_rows)
        return resolved_version

    def load_citas_features(self, version: str) -> list[Any]:
        return self._feature_store.load(self.CITAS_DATASET_NAME, version)

    def list_citas_versions(self) -> list[str]:
        return self._feature_store.list_versions(self.CITAS_DATASET_NAME)

    def _build_version(self) -> str:
        now_utc = datetime.now(tz=timezone.utc)
        return now_utc.strftime("%Y-%m-%dT%H-%M-%S")


def _to_serializable(row: Any) -> Any:
    if is_dataclass(row):
        return asdict(row)
    return row

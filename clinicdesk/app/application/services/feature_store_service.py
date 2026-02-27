from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.ml_artifacts.feature_artifacts import (
    FeatureArtifactMetadata,
    build_schema_from_dataclass,
    canonical_json_bytes,
    compute_content_hash,
    compute_schema_hash,
)
from clinicdesk.app.application.ports.feature_store_port import FeatureStorePort


class FeatureStoreService:
    """Servicio liviano para gestión del dataset de features de citas."""

    CITAS_DATASET_NAME = "citas_features"
    CITAS_SCHEMA_VERSION = "v1"

    def __init__(self, feature_store: FeatureStorePort) -> None:
        self._feature_store = feature_store

    def save_citas_features(self, rows: list[Any], version: str | None = None) -> str:
        resolved_version = version or self._build_version()
        serialized_rows = [_to_serializable(row) for row in rows]
        self._feature_store.save(self.CITAS_DATASET_NAME, resolved_version, serialized_rows)
        return resolved_version

    def save_citas_features_with_artifacts(
        self,
        rows: list[CitasFeatureRow],
        quality_report: CitasFeatureQualityReport,
        version: str | None = None,
    ) -> str:
        resolved_version = version or self._build_version()
        serialized_rows = [_to_serializable(row) for row in rows]
        schema = build_schema_from_dataclass(CitasFeatureRow, version=self.CITAS_SCHEMA_VERSION)
        rows_bytes = canonical_json_bytes(serialized_rows)
        metadata = FeatureArtifactMetadata(
            dataset_name=self.CITAS_DATASET_NAME,
            version=resolved_version,
            created_at=self._build_created_at(),
            row_count=len(serialized_rows),
            content_hash=compute_content_hash(rows_bytes),
            schema_hash=compute_schema_hash(schema),
            schema_version=schema.version,
            quality=_to_serializable(quality_report),
        )
        self._feature_store.save_with_metadata(
            self.CITAS_DATASET_NAME,
            resolved_version,
            serialized_rows,
            metadata,
        )
        return resolved_version

    def load_citas_features(self, version: str) -> list[Any]:
        return self._feature_store.load(self.CITAS_DATASET_NAME, version)

    def load_citas_features_metadata(self, version: str) -> FeatureArtifactMetadata:
        return self._feature_store.load_metadata(self.CITAS_DATASET_NAME, version)

    def list_citas_versions(self) -> list[str]:
        return self._feature_store.list_versions(self.CITAS_DATASET_NAME)

    def _build_version(self) -> str:
        now_utc = datetime.now(tz=timezone.utc)
        return now_utc.strftime("%Y-%m-%dT%H-%M-%S")

    def _build_created_at(self) -> str:
        return datetime.now(tz=timezone.utc).isoformat()


def _to_serializable(row: Any) -> Any:
    if is_dataclass(row):
        return asdict(row)
    return row

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clinicdesk.app.application.ml_artifacts.feature_artifacts import (
    FeatureArtifactMetadata,
    FeatureSchema,
    FeatureSchemaField,
    canonical_json_bytes,
    compute_content_hash,
    compute_schema_hash,
    feature_metadata_from_dict,
    feature_metadata_to_dict,
    feature_schema_from_dict,
    feature_schema_to_dict,
)
from clinicdesk.app.application.ports.feature_store_port import FeatureStorePort


class FeatureStoreDatasetNotFoundError(FileNotFoundError):
    """Error cuando el dataset solicitado no existe."""


class FeatureStoreVersionNotFoundError(FileNotFoundError):
    """Error cuando la versión solicitada no existe."""


class FeatureStoreMetadataNotFoundError(FileNotFoundError):
    """Error cuando la metadata solicitada no existe."""


class FeatureStoreSchemaNotFoundError(FileNotFoundError):
    """Error cuando el schema solicitado no existe."""


class LocalJsonFeatureStore(FeatureStorePort):
    """Implementación local simple de feature store en archivos JSON."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def save(self, dataset_name: str, version: str, rows: list[Any]) -> None:
        file_path = self._version_file_path(dataset_name, version)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._build_payload(rows)
        self._write_json_file(file_path, payload)

    def load(self, dataset_name: str, version: str) -> list[Any]:
        file_path = self._version_file_path(dataset_name, version)
        if not file_path.parent.exists():
            raise FeatureStoreDatasetNotFoundError(f"Dataset no existe: '{dataset_name}'.")
        if not file_path.exists():
            raise FeatureStoreVersionNotFoundError(
                f"Versión '{version}' no existe para dataset '{dataset_name}'."
            )
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return self._validate_loaded_payload(data, dataset_name, version)

    def list_versions(self, dataset_name: str) -> list[str]:
        dataset_path = self._dataset_path(dataset_name)
        if not dataset_path.exists():
            raise FeatureStoreDatasetNotFoundError(f"Dataset no existe: '{dataset_name}'.")
        versions = [
            path.stem
            for path in dataset_path.glob("*.json")
            if path.is_file() and not path.name.endswith((".metadata.json", ".schema.json"))
        ]
        return sorted(versions)

    def save_with_metadata(
        self,
        dataset_name: str,
        version: str,
        rows: list[Any],
        metadata: FeatureArtifactMetadata,
    ) -> None:
        payload = self._build_payload(rows)
        rows_bytes = canonical_json_bytes(payload)
        schema = self._build_schema(payload, metadata.schema_version)
        resolved_metadata = self._build_resolved_metadata(metadata, rows_bytes, schema)

        version_file = self._version_file_path(dataset_name, version)
        schema_file = self._schema_file_path(dataset_name, version)
        metadata_file = self._metadata_file_path(dataset_name, version)
        version_file.parent.mkdir(parents=True, exist_ok=True)

        version_file.write_bytes(rows_bytes)
        self._write_json_file(schema_file, feature_schema_to_dict(schema))
        self._write_json_file(metadata_file, feature_metadata_to_dict(resolved_metadata))

    def load_metadata(self, dataset_name: str, version: str) -> FeatureArtifactMetadata:
        metadata_file = self._metadata_file_path(dataset_name, version)
        if not metadata_file.exists():
            raise FeatureStoreMetadataNotFoundError(
                f"Metadata no existe para dataset '{dataset_name}' versión '{version}'."
            )
        with metadata_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return feature_metadata_from_dict(payload)

    def load_schema(self, dataset_name: str, version: str) -> FeatureSchema:
        schema_file = self._schema_file_path(dataset_name, version)
        if not schema_file.exists():
            raise FeatureStoreSchemaNotFoundError(
                f"Schema no existe para dataset '{dataset_name}' versión '{version}'."
            )
        with schema_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return feature_schema_from_dict(payload)

    def _dataset_path(self, dataset_name: str) -> Path:
        return self._base_path / dataset_name

    def _version_file_path(self, dataset_name: str, version: str) -> Path:
        return self._dataset_path(dataset_name) / f"{version}.json"

    def _metadata_file_path(self, dataset_name: str, version: str) -> Path:
        return self._dataset_path(dataset_name) / f"{version}.metadata.json"

    def _schema_file_path(self, dataset_name: str, version: str) -> Path:
        return self._dataset_path(dataset_name) / f"{version}.schema.json"

    def _build_payload(self, rows: list[Any]) -> list[Any]:
        return rows

    def _build_schema(self, rows: list[Any], version: str) -> FeatureSchema:
        if not rows:
            return FeatureSchema(version=version, fields=[])
        first_row = rows[0]
        if not isinstance(first_row, dict):
            return FeatureSchema(version=version, fields=[])
        return FeatureSchema(
            version=version,
            fields=[FeatureSchemaField(name=key, type=type(value).__name__) for key, value in first_row.items()],
        )

    def _build_resolved_metadata(
        self,
        metadata: FeatureArtifactMetadata,
        rows_bytes: bytes,
        schema: FeatureSchema,
    ) -> FeatureArtifactMetadata:
        return FeatureArtifactMetadata(
            dataset_name=metadata.dataset_name,
            version=metadata.version,
            created_at=metadata.created_at,
            row_count=metadata.row_count,
            content_hash=compute_content_hash(rows_bytes),
            schema_hash=compute_schema_hash(schema),
            schema_version=metadata.schema_version,
            quality=metadata.quality,
        )

    def _validate_loaded_payload(self, data: Any, dataset_name: str, version: str) -> list[Any]:
        if not isinstance(data, list):
            raise ValueError(
                f"Contenido inválido para dataset '{dataset_name}' versión '{version}': se esperaba list."
            )
        return data

    def _write_json_file(self, path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

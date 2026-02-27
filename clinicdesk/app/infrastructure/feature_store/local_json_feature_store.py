from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clinicdesk.app.application.ports.feature_store_port import FeatureStorePort


class FeatureStoreDatasetNotFoundError(FileNotFoundError):
    """Error cuando el dataset solicitado no existe."""


class FeatureStoreVersionNotFoundError(FileNotFoundError):
    """Error cuando la versión solicitada no existe."""


class LocalJsonFeatureStore(FeatureStorePort):
    """Implementación local simple de feature store en archivos JSON."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def save(self, dataset_name: str, version: str, rows: list[Any]) -> None:
        file_path = self._version_file_path(dataset_name, version)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._build_payload(rows)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

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
        versions = [path.stem for path in dataset_path.glob("*.json") if path.is_file()]
        return sorted(versions)

    def _dataset_path(self, dataset_name: str) -> Path:
        return self._base_path / dataset_name

    def _version_file_path(self, dataset_name: str, version: str) -> Path:
        return self._dataset_path(dataset_name) / f"{version}.json"

    def _build_payload(self, rows: list[Any]) -> list[Any]:
        return rows

    def _validate_loaded_payload(self, data: Any, dataset_name: str, version: str) -> list[Any]:
        if not isinstance(data, list):
            raise ValueError(
                f"Contenido inválido para dataset '{dataset_name}' versión '{version}': se esperaba list."
            )
        return data

from __future__ import annotations

from typing import Any, Protocol

from clinicdesk.app.application.ml_artifacts.feature_artifacts import FeatureArtifactMetadata


class FeatureStorePort(Protocol):
    """Contrato para almacenar y recuperar datasets versionados de features."""

    def save(self, dataset_name: str, version: str, rows: list[Any]) -> None:
        """Persiste una versión completa de un dataset."""

    def load(self, dataset_name: str, version: str) -> list[Any]:
        """Carga una versión específica de un dataset."""

    def save_with_metadata(
        self,
        dataset_name: str,
        version: str,
        rows: list[Any],
        metadata: FeatureArtifactMetadata,
    ) -> None:
        """Persiste una versión de dataset junto a metadata y schema."""

    def load_metadata(self, dataset_name: str, version: str) -> FeatureArtifactMetadata:
        """Carga metadata de una versión específica de un dataset."""

    def list_versions(self, dataset_name: str) -> list[str]:
        """Lista versiones disponibles para un dataset."""

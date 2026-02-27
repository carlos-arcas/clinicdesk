from __future__ import annotations

from typing import Any, Protocol


class ModelStorePort(Protocol):
    """Contrato para almacenar modelos versionados offline."""

    def save_model(
        self,
        model_name: str,
        version: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        ...

    def load_model(self, model_name: str, version: str) -> tuple[dict[str, Any], dict[str, Any]]:
        ...

    def list_model_versions(self, model_name: str) -> list[str]:
        ...

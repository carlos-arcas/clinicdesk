from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from clinicdesk.app.application.ports.model_store_port import ModelStorePort


class ModelStoreNotFoundError(FileNotFoundError):
    """Error cuando no existe modelo o versión solicitada."""


class LocalJsonModelStore(ModelStorePort):
    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def save_model(
        self,
        model_name: str,
        version: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        model_dir = self._model_dir(model_name)
        model_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self._payload_file(model_name, version), payload)
        self._write_json(self._metadata_file(model_name, version), metadata)

    def load_model(self, model_name: str, version: str) -> tuple[dict[str, Any], dict[str, Any]]:
        payload_file = self._payload_file(model_name, version)
        metadata_file = self._metadata_file(model_name, version)
        if not payload_file.exists() or not metadata_file.exists():
            raise ModelStoreNotFoundError(
                f"Modelo '{model_name}' versión '{version}' no existe en model store."
            )
        return self._read_json(payload_file), self._read_json(metadata_file)

    def list_model_versions(self, model_name: str) -> list[str]:
        model_dir = self._model_dir(model_name)
        if not model_dir.exists():
            return []
        versions = [
            path.name[: -len(".model.json")]
            for path in model_dir.glob("*.model.json")
            if path.is_file()
        ]
        return sorted(versions)

    def _model_dir(self, model_name: str) -> Path:
        return self._base_path / "models" / model_name

    def _payload_file(self, model_name: str, version: str) -> Path:
        return self._model_dir(model_name) / f"{version}.model.json"

    def _metadata_file(self, model_name: str, version: str) -> Path:
        return self._model_dir(model_name) / f"{version}.metadata.json"

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _read_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError(f"Payload inválido en '{path.name}': se esperaba objeto JSON.")
        return loaded

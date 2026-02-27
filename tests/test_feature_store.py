from __future__ import annotations

import json

import pytest

from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import (
    FeatureStoreDatasetNotFoundError,
    FeatureStoreVersionNotFoundError,
    LocalJsonFeatureStore,
)


def test_feature_store_save_load_roundtrip(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    service = FeatureStoreService(store)
    rows = [
        {"cita_id": "c1", "duracion_min": 10, "estado_norm": "programada"},
        {"cita_id": "c2", "duracion_min": 30, "estado_norm": "realizada"},
    ]

    version = service.save_citas_features(rows, version="2026-02-27T21-30-00")
    loaded = service.load_citas_features(version)

    assert version == "2026-02-27T21-30-00"
    assert loaded == rows


def test_feature_store_list_versions_returns_sorted_versions(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    service = FeatureStoreService(store)

    service.save_citas_features([{"cita_id": "a"}], version="2026-02-27T21-00-00")
    service.save_citas_features([{"cita_id": "b"}], version="2026-02-27T20-00-00")

    assert service.list_citas_versions() == ["2026-02-27T20-00-00", "2026-02-27T21-00-00"]


def test_feature_store_load_missing_version_raises_explicit_error(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)

    with pytest.raises(FeatureStoreDatasetNotFoundError, match="Dataset no existe"):
        store.load("citas_features", "2026-02-27T21-30-00")

    store.save("citas_features", "2026-02-27T21-00-00", [{"id": 1}])

    with pytest.raises(FeatureStoreVersionNotFoundError, match="Versión"):
        store.load("citas_features", "2026-02-27T21-30-00")


def test_feature_store_save_two_versions_does_not_overwrite(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    dataset = "citas_features"

    store.save(dataset, "2026-02-27T21-00-00", [{"id": "v1"}])
    store.save(dataset, "2026-02-27T22-00-00", [{"id": "v2"}])

    assert store.load(dataset, "2026-02-27T21-00-00") == [{"id": "v1"}]
    assert store.load(dataset, "2026-02-27T22-00-00") == [{"id": "v2"}]


def test_feature_store_serialization_is_deterministic_for_same_content_and_version(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    dataset = "citas_features"
    version = "2026-02-27T23-00-00"
    rows = [{"z": 1, "a": 2}, {"b": [3, 2, 1], "c": {"y": 1, "x": 2}}]

    store.save(dataset, version, rows)
    payload_path = tmp_path / dataset / f"{version}.json"
    first_content = payload_path.read_text(encoding="utf-8")

    store.save(dataset, version, rows)
    second_content = payload_path.read_text(encoding="utf-8")

    assert first_content == second_content
    assert json.loads(first_content) == rows

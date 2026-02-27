from __future__ import annotations

from clinicdesk.app.infrastructure.model_store.local_json_model_store import LocalJsonModelStore


def test_model_store_save_load_and_list_versions(tmp_path) -> None:
    store = LocalJsonModelStore(tmp_path)
    payload = {"weights": {"f": 1.2}}
    metadata = {"schema_hash": "abc", "metrics": {"accuracy": 1.0}}

    store.save_model("citas_nb_v1", "v1", payload, metadata)
    store.save_model("citas_nb_v1", "v2", payload, metadata)

    loaded_payload, loaded_metadata = store.load_model("citas_nb_v1", "v1")
    assert loaded_payload == payload
    assert loaded_metadata == metadata
    assert store.list_model_versions("citas_nb_v1") == ["v1", "v2"]

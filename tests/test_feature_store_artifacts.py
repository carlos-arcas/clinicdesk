from __future__ import annotations

import json
from dataclasses import asdict

import pytest

from clinicdesk.app.application.features.citas_features import CitasFeatureQualityReport, CitasFeatureRow
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.ml_artifacts.feature_artifacts import (
    build_schema_from_dataclass,
    canonical_json_bytes,
    compute_content_hash,
    compute_schema_hash,
)
from clinicdesk.app.application.services.feature_store_service import FeatureStoreService
from clinicdesk.app.application.usecases.score_citas import (
    ScoreCitas,
    ScoreCitasRequest,
    ScoringValidationError,
)
from clinicdesk.app.infrastructure.feature_store.local_json_feature_store import (
    FeatureStoreMetadataNotFoundError,
    LocalJsonFeatureStore,
)


def _quality(total: int) -> CitasFeatureQualityReport:
    return CitasFeatureQualityReport(
        total=total,
        suspicious_count=0,
        missing_count=0,
        by_estado={"programada": total},
        by_duracion_bucket={"21-40": total},
        by_notas_bucket={"1-20": total},
    )


def _row(cita_id: str) -> CitasFeatureRow:
    return CitasFeatureRow(
        cita_id=cita_id,
        duracion_min=30,
        duracion_bucket="21-40",
        hora_inicio=9,
        dia_semana=2,
        is_weekend=False,
        notas_len=10,
        notas_len_bucket="1-20",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=False,
    )


def test_save_with_metadata_creates_three_files_and_load_metadata(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    service = FeatureStoreService(store)
    version = service.save_citas_features_with_artifacts([_row("c1")], _quality(1), version="v1")

    base = tmp_path / "citas_features"
    assert (base / f"{version}.json").exists()
    assert (base / f"{version}.metadata.json").exists()
    assert (base / f"{version}.schema.json").exists()

    metadata = service.load_citas_features_metadata(version)
    assert metadata.version == "v1"
    assert metadata.row_count == 1
    assert metadata.quality["total"] == 1


def test_content_hash_is_deterministic_for_same_content_and_version(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    service = FeatureStoreService(store)
    rows = [_row("a"), _row("b")]

    service.save_citas_features_with_artifacts(rows, _quality(2), version="v1")
    first = service.load_citas_features_metadata("v1")
    service.save_citas_features_with_artifacts(rows, _quality(2), version="v1")
    second = service.load_citas_features_metadata("v1")

    assert first.content_hash == second.content_hash
    expected_hash = compute_content_hash(canonical_json_bytes([asdict(item) for item in rows]))
    assert first.content_hash == expected_hash


def test_schema_hash_is_stable_and_contains_expected_fields() -> None:
    schema = build_schema_from_dataclass(CitasFeatureRow, version="v1")

    assert compute_schema_hash(schema) == compute_schema_hash(schema)
    assert [item.name for item in schema.fields] == [
        "cita_id",
        "duracion_min",
        "duracion_bucket",
        "hora_inicio",
        "dia_semana",
        "is_weekend",
        "notas_len",
        "notas_len_bucket",
        "has_incidencias",
        "estado_norm",
        "is_suspicious",
        "inicio_ts",
    ]


def test_load_metadata_missing_raises_explicit_error(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)

    with pytest.raises(FeatureStoreMetadataNotFoundError, match="Metadata no existe"):
        store.load_metadata("citas_features", "missing")


def test_score_citas_raises_when_metadata_row_count_mismatch(tmp_path) -> None:
    store = LocalJsonFeatureStore(tmp_path)
    service = FeatureStoreService(store)
    service.save_citas_features_with_artifacts([_row("c1")], _quality(1), version="v1")

    metadata_path = tmp_path / "citas_features" / "v1.metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["row_count"] = 99
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    usecase = ScoreCitas(service, BaselineCitasPredictor())
    with pytest.raises(ScoringValidationError, match="row_count"):
        usecase.execute(ScoreCitasRequest(dataset_version="v1"))

from __future__ import annotations

from dataclasses import asdict

import pytest

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor
from clinicdesk.app.application.usecases.score_citas import (
    ScoreCitas,
    ScoreCitasRequest,
    ScoringDatasetNotFoundError,
)


class FakeFeatureStoreService:
    def __init__(self, payload_by_version: dict[str, list[dict]]) -> None:
        self._payload_by_version = payload_by_version

    def load_citas_features(self, version: str) -> list[dict]:
        if version not in self._payload_by_version:
            raise FileNotFoundError(version)
        return self._payload_by_version[version]


def _row(cita_id: str, **overrides: object) -> dict:
    base = CitasFeatureRow(
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
    payload = asdict(base)
    payload.update(overrides)
    return payload


def test_score_citas_returns_items_with_matching_cita_id() -> None:
    fake_store = FakeFeatureStoreService({"v1": [_row("c-1"), _row("c-2")]})
    usecase = ScoreCitas(fake_store, BaselineCitasPredictor())

    response = usecase.execute(ScoreCitasRequest(dataset_version="v1"))

    assert response.version == "v1"
    assert response.total == 2
    assert [item.cita_id for item in response.items] == ["c-1", "c-2"]


def test_score_citas_raises_explicit_error_for_missing_version() -> None:
    fake_store = FakeFeatureStoreService({"v1": [_row("c-1")]})
    usecase = ScoreCitas(fake_store, BaselineCitasPredictor())

    with pytest.raises(ScoringDatasetNotFoundError, match="No se pudo cargar dataset"):
        usecase.execute(ScoreCitasRequest(dataset_version="missing"))


def test_score_citas_limit_returns_only_requested_rows() -> None:
    fake_store = FakeFeatureStoreService({"v2": [_row("a"), _row("b"), _row("c")]})
    usecase = ScoreCitas(fake_store, BaselineCitasPredictor())

    response = usecase.execute(ScoreCitasRequest(dataset_version="v2", limit=2))

    assert response.total == 2
    assert [item.cita_id for item in response.items] == ["a", "b"]

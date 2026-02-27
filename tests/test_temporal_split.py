from __future__ import annotations

import pytest

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.splitting import (
    TemporalSplitConfig,
    TemporalSplitNotEnoughDataError,
    temporal_folds,
    temporal_train_test_split,
)


def _row(idx: int) -> CitasFeatureRow:
    return CitasFeatureRow(
        cita_id=f"c{idx}",
        duracion_min=20,
        duracion_bucket="11-20",
        hora_inicio=9,
        dia_semana=idx % 7,
        is_weekend=False,
        notas_len=idx,
        notas_len_bucket="1-20",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=False,
        inicio_ts=1_700_000_000 + idx,
    )


def test_temporal_train_test_split_is_deterministic() -> None:
    rows = [_row(idx) for idx in range(10)]
    cfg = TemporalSplitConfig(test_ratio=0.2, min_train=5, time_field="inicio_ts")

    train_rows, test_rows = temporal_train_test_split(list(reversed(rows)), cfg)

    assert len(train_rows) == 8
    assert len(test_rows) == 2
    assert [row.cita_id for row in train_rows] == [f"c{idx}" for idx in range(8)]
    assert [row.cita_id for row in test_rows] == ["c8", "c9"]


def test_temporal_split_raises_for_not_enough_data() -> None:
    rows = [_row(idx) for idx in range(10)]
    cfg = TemporalSplitConfig(test_ratio=0.2, min_train=20, time_field="inicio_ts")

    with pytest.raises(TemporalSplitNotEnoughDataError, match="min_train"):
        temporal_train_test_split(rows, cfg)


def test_temporal_folds_returns_deterministic_walk_forward_windows() -> None:
    rows = [_row(idx) for idx in range(30)]

    folds = temporal_folds(list(reversed(rows)), n_folds=3, min_train=10)

    assert len(folds) == 3
    assert (len(folds[0][0]), len(folds[0][1])) == (18, 6)
    assert (len(folds[1][0]), len(folds[1][1])) == (24, 6)
    assert (len(folds[2][0]), len(folds[2][1])) == (27, 3)
    assert folds[0][1][0].cita_id == "c18"

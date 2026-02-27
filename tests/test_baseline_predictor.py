from __future__ import annotations

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.baseline_citas_predictor import BaselineCitasPredictor


def _feature(**overrides: object) -> CitasFeatureRow:
    base = dict(
        cita_id="c-1",
        duracion_min=10,
        duracion_bucket="0-10",
        hora_inicio=10,
        dia_semana=1,
        is_weekend=False,
        notas_len=0,
        notas_len_bucket="0",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=False,
    )
    base.update(overrides)
    return CitasFeatureRow(**base)


def test_predictor_returns_expected_score_and_label_for_low_signal() -> None:
    predictor = BaselineCitasPredictor()

    result = predictor.predict_one(_feature())

    assert result.score == 0.05
    assert result.label == "low"
    assert result.reasons == ["baseline_low_signal"]


def test_predictor_clamps_score_and_keeps_traceable_reasons() -> None:
    predictor = BaselineCitasPredictor()
    row = _feature(
        duracion_bucket="41+",
        notas_len_bucket="101+",
        has_incidencias=True,
        is_suspicious=True,
        is_weekend=True,
        estado_norm="no_show",
    )

    result = predictor.predict_one(row)

    assert result.score == 1.0
    assert result.label == "high"
    assert "has_incidencias" in result.reasons
    assert "is_suspicious" in result.reasons
    assert "duracion_bucket=41+" in result.reasons
    assert "notas_bucket=101+" in result.reasons
    assert "estado_no_show" in result.reasons

from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.application.features.citas_features import (
    CitasFeatureRow,
    CitasFeatureValidationError,
    build_citas_features,
    compute_citas_quality_report,
    validate_citas_features,
)
from clinicdesk.app.application.pipelines.build_citas_dataset import CitasDatasetRow


def test_build_citas_features_happy_path() -> None:
    rows = [
        CitasDatasetRow(
            cita_id="1",
            paciente_id=10,
            medico_id=20,
            inicio=datetime(2024, 5, 20, 9, 0),
            fin=datetime(2024, 5, 20, 9, 30),
            duracion_min=30,
            estado="PROGRAMADA",
            has_incidencias=False,
            notas_len=12,
        ),
        CitasDatasetRow(
            cita_id="2",
            paciente_id=11,
            medico_id=20,
            inicio=datetime(2024, 5, 25, 10, 0),
            fin=datetime(2024, 5, 25, 10, 45),
            duracion_min=45,
            estado="REALIZADA",
            has_incidencias=True,
            notas_len=44,
        ),
    ]

    features = build_citas_features(rows)

    assert len(features) == 2
    assert features[0].duracion_bucket == "21-40"
    assert features[0].hora_inicio == 9
    assert features[0].dia_semana == 0
    assert features[0].is_weekend is False
    assert features[1].duracion_bucket == "41+"
    assert features[1].is_weekend is True


def test_build_citas_features_maps_notas_len_none_or_zero_to_bucket_zero() -> None:
    rows = [
        CitasDatasetRow(
            cita_id="zero",
            paciente_id=1,
            medico_id=2,
            inicio=datetime(2024, 5, 20, 9, 0),
            fin=datetime(2024, 5, 20, 9, 10),
            duracion_min=10,
            estado="PROGRAMADA",
            has_incidencias=False,
            notas_len=0,
        ),
        CitasDatasetRow(
            cita_id="negative",
            paciente_id=1,
            medico_id=2,
            inicio=datetime(2024, 5, 20, 11, 0),
            fin=datetime(2024, 5, 20, 11, 10),
            duracion_min=10,
            estado="PROGRAMADA",
            has_incidencias=False,
            notas_len=-5,
        ),
    ]

    features = build_citas_features(rows)

    assert [row.notas_len_bucket for row in features] == ["0", "0"]
    assert [row.notas_len for row in features] == [0, 0]


def test_build_citas_features_marks_outlier_duration_as_suspicious() -> None:
    rows = [
        CitasDatasetRow(
            cita_id="outlier",
            paciente_id=1,
            medico_id=2,
            inicio=datetime(2024, 5, 20, 9, 0),
            fin=datetime(2024, 5, 20, 17, 20),
            duracion_min=500,
            estado="REALIZADA",
            has_incidencias=False,
            notas_len=10,
        )
    ]

    feature = build_citas_features(rows)[0]

    assert feature.is_suspicious is True


def test_validate_citas_features_raises_on_impossible_duration_for_non_cancelled() -> None:
    invalid_feature = CitasFeatureRow(
        cita_id="bad",
        duracion_min=0,
        duracion_bucket="0-10",
        hora_inicio=11,
        dia_semana=2,
        is_weekend=False,
        notas_len=0,
        notas_len_bucket="0",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=True,
    )

    with pytest.raises(CitasFeatureValidationError, match="duracion_min"):
        validate_citas_features([invalid_feature])


def test_compute_citas_quality_report_counts_buckets_estado_and_suspicious() -> None:
    features = [
        CitasFeatureRow(
            cita_id="1",
            duracion_min=20,
            duracion_bucket="11-20",
            hora_inicio=8,
            dia_semana=0,
            is_weekend=False,
            notas_len=0,
            notas_len_bucket="0",
            has_incidencias=False,
            estado_norm="programada",
            is_suspicious=False,
        ),
        CitasFeatureRow(
            cita_id="2",
            duracion_min=500,
            duracion_bucket="41+",
            hora_inicio=9,
            dia_semana=6,
            is_weekend=True,
            notas_len=30,
            notas_len_bucket="21-100",
            has_incidencias=True,
            estado_norm="realizada",
            is_suspicious=True,
        ),
        CitasFeatureRow(
            cita_id="3",
            duracion_min=15,
            duracion_bucket="11-20",
            hora_inicio=10,
            dia_semana=2,
            is_weekend=False,
            notas_len=5,
            notas_len_bucket="1-20",
            has_incidencias=False,
            estado_norm="desconocido",
            is_suspicious=False,
        ),
    ]

    report = compute_citas_quality_report(features)

    assert report.total == 3
    assert report.suspicious_count == 1
    assert report.missing_count == 1
    assert report.by_estado == {"programada": 1, "realizada": 1, "desconocido": 1}
    assert report.by_duracion_bucket == {"11-20": 2, "41+": 1}
    assert report.by_notas_bucket == {"0": 1, "21-100": 1, "1-20": 1}

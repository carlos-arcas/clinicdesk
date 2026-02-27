from __future__ import annotations

from clinicdesk.app.application.features.citas_features import CitasFeatureRow
from clinicdesk.app.application.ml.drift import compute_citas_drift


def _row(cita_id: str, duracion_bucket: str) -> CitasFeatureRow:
    return CitasFeatureRow(
        cita_id=cita_id,
        duracion_min=30,
        duracion_bucket=duracion_bucket,
        hora_inicio=9,
        dia_semana=2,
        is_weekend=False,
        notas_len=10,
        notas_len_bucket="1-20",
        has_incidencias=False,
        estado_norm="programada",
        is_suspicious=False,
        inicio_ts=1_700_000_000,
    )


def test_compute_citas_drift_detects_strong_shift_and_psi_flag() -> None:
    from_rows = [_row(f"f{idx}", "11-20") for idx in range(12)]
    to_rows = [_row(f"t{idx}", "41+") for idx in range(12)]

    report = compute_citas_drift(from_rows, to_rows, from_version="v1", to_version="v2")

    assert report.from_version == "v1"
    assert report.to_version == "v2"
    assert report.feature_shifts["duracion_bucket"]["11-20"] == -1.0
    assert report.feature_shifts["duracion_bucket"]["41+"] == 1.0
    assert report.psi_by_feature["duracion_bucket"] > 0.2
    assert report.overall_flag is True

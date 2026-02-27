from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from clinicdesk.app.application.pipelines.build_citas_dataset import CitasDatasetRow


@dataclass(slots=True)
class CitasFeatureRow:
    cita_id: str
    duracion_min: int
    duracion_bucket: str
    hora_inicio: int
    dia_semana: int
    is_weekend: bool
    notas_len: int
    notas_len_bucket: str
    has_incidencias: bool
    estado_norm: str
    is_suspicious: bool


@dataclass(slots=True)
class CitasFeatureQualityReport:
    total: int
    suspicious_count: int
    missing_count: int
    by_estado: dict[str, int]
    by_duracion_bucket: dict[str, int]
    by_notas_bucket: dict[str, int]


class CitasFeatureValidationError(ValueError):
    """Error explícito de validación de features de citas."""


def build_citas_features(
    rows: list[CitasDatasetRow], *, now: datetime | None = None
) -> list[CitasFeatureRow]:
    _ = now
    features = [
        CitasFeatureRow(
            cita_id=row.cita_id,
            duracion_min=row.duracion_min,
            duracion_bucket=_duracion_bucket(row.duracion_min),
            hora_inicio=row.inicio.hour,
            dia_semana=row.inicio.weekday(),
            is_weekend=row.inicio.weekday() >= 5,
            notas_len=max(row.notas_len, 0),
            notas_len_bucket=_notas_len_bucket(row.notas_len),
            has_incidencias=bool(row.has_incidencias),
            estado_norm=_normalize_estado(row.estado),
            is_suspicious=_is_suspicious(row),
        )
        for row in rows
    ]
    validate_citas_features(features)
    return features


def validate_citas_features(rows: list[CitasFeatureRow]) -> None:
    for row in rows:
        if row.hora_inicio < 0 or row.hora_inicio > 23:
            raise CitasFeatureValidationError(
                f"Feature inválida para cita '{row.cita_id}': hora_inicio fuera de rango."
            )
        if row.dia_semana < 0 or row.dia_semana > 6:
            raise CitasFeatureValidationError(
                f"Feature inválida para cita '{row.cita_id}': dia_semana fuera de rango."
            )
        if row.notas_len_bucket != _notas_len_bucket(row.notas_len):
            raise CitasFeatureValidationError(
                f"Feature inválida para cita '{row.cita_id}': notas_len_bucket inconsistente."
            )
        if row.duracion_min <= 0 and row.estado_norm != "cancelada":
            raise CitasFeatureValidationError(
                f"Feature inválida para cita '{row.cita_id}': duracion_min debe ser > 0 fuera de canceladas."
            )


def compute_citas_quality_report(features: list[CitasFeatureRow]) -> CitasFeatureQualityReport:
    by_estado: dict[str, int] = {}
    by_duracion_bucket: dict[str, int] = {}
    by_notas_bucket: dict[str, int] = {}

    for row in features:
        by_estado[row.estado_norm] = by_estado.get(row.estado_norm, 0) + 1
        by_duracion_bucket[row.duracion_bucket] = by_duracion_bucket.get(row.duracion_bucket, 0) + 1
        by_notas_bucket[row.notas_len_bucket] = by_notas_bucket.get(row.notas_len_bucket, 0) + 1

    return CitasFeatureQualityReport(
        total=len(features),
        suspicious_count=sum(1 for row in features if row.is_suspicious),
        missing_count=sum(1 for row in features if row.estado_norm == "desconocido"),
        by_estado=by_estado,
        by_duracion_bucket=by_duracion_bucket,
        by_notas_bucket=by_notas_bucket,
    )


def _duracion_bucket(duracion_min: int) -> str:
    if duracion_min <= 10:
        return "0-10"
    if duracion_min <= 20:
        return "11-20"
    if duracion_min <= 40:
        return "21-40"
    return "41+"


def _notas_len_bucket(notas_len: int) -> str:
    if notas_len <= 0:
        return "0"
    if notas_len <= 20:
        return "1-20"
    if notas_len <= 100:
        return "21-100"
    return "101+"


def _normalize_estado(estado: str) -> str:
    normalized = (estado or "").strip().casefold().replace(" ", "_")
    if not normalized:
        return "desconocido"
    aliases = {
        "programada": "programada",
        "realizada": "realizada",
        "cancelada": "cancelada",
        "cancelado": "cancelada",
        "no_show": "no_show",
        "noshow": "no_show",
    }
    return aliases.get(normalized, normalized)


def _is_suspicious(row: CitasDatasetRow) -> bool:
    estado_norm = _normalize_estado(row.estado)
    non_positive_invalid = row.duracion_min <= 0 and estado_norm != "cancelada"
    too_long = row.duracion_min > 240
    return non_positive_invalid or too_long

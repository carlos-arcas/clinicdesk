from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3


_SQL_KPIS_POR_DIA = """
WITH base AS (
    SELECT
        id,
        date(inicio) AS fecha,
        check_in_at,
        llamado_a_consulta_at,
        consulta_inicio_at,
        consulta_fin_at,
        check_out_at,
        CASE
            WHEN check_in_at IS NOT NULL AND llamado_a_consulta_at IS NOT NULL
            THEN (julianday(llamado_a_consulta_at) - julianday(check_in_at)) * 24.0 * 60.0
        END AS espera_min,
        CASE
            WHEN consulta_inicio_at IS NOT NULL AND consulta_fin_at IS NOT NULL
            THEN (julianday(consulta_fin_at) - julianday(consulta_inicio_at)) * 24.0 * 60.0
        END AS consulta_min,
        CASE
            WHEN check_in_at IS NOT NULL AND check_out_at IS NOT NULL
            THEN (julianday(check_out_at) - julianday(check_in_at)) * 24.0 * 60.0
        END AS total_clinica_min,
        CASE
            WHEN consulta_inicio_at IS NOT NULL AND inicio IS NOT NULL
            THEN (julianday(consulta_inicio_at) - julianday(inicio)) * 24.0 * 60.0
        END AS retraso_min
    FROM citas
    WHERE activo = 1
      AND date(inicio) BETWEEN date(?) AND date(?)
)
SELECT
    fecha,
    COUNT(1) AS total_citas,
    SUM(CASE WHEN check_in_at IS NOT NULL THEN 1 ELSE 0 END) AS total_con_checkin,
    SUM(CASE WHEN espera_min IS NOT NULL AND espera_min >= 0 THEN 1 ELSE 0 END) AS total_validas_espera,
    AVG(CASE WHEN espera_min IS NOT NULL AND espera_min >= 0 THEN espera_min END) AS espera_media_min,
    SUM(CASE WHEN consulta_min IS NOT NULL AND consulta_min >= 0 THEN 1 ELSE 0 END) AS total_validas_consulta,
    AVG(CASE WHEN consulta_min IS NOT NULL AND consulta_min >= 0 THEN consulta_min END) AS consulta_media_min,
    SUM(CASE WHEN total_clinica_min IS NOT NULL AND total_clinica_min >= 0 THEN 1 ELSE 0 END) AS total_validas_total_clinica,
    AVG(CASE WHEN total_clinica_min IS NOT NULL AND total_clinica_min >= 0 THEN total_clinica_min END) AS total_clinica_media_min,
    SUM(CASE WHEN retraso_min IS NOT NULL AND retraso_min >= 0 THEN 1 ELSE 0 END) AS total_validas_retraso,
    AVG(CASE WHEN retraso_min IS NOT NULL AND retraso_min >= 0 THEN retraso_min END) AS retraso_media_min,
    SUM(
        CASE
            WHEN (espera_min IS NOT NULL AND espera_min < 0)
              OR (consulta_min IS NOT NULL AND consulta_min < 0)
              OR (total_clinica_min IS NOT NULL AND total_clinica_min < 0)
              OR (retraso_min IS NOT NULL AND retraso_min < 0)
            THEN 1 ELSE 0
        END
    ) AS descartados
FROM base
GROUP BY fecha
ORDER BY fecha ASC
"""

_SQL_KPIS_POR_MEDICO = """
WITH base AS (
    SELECT
        c.medico_id,
        m.nombre || ' ' || m.apellidos AS medico_nombre,
        c.estado,
        CASE
            WHEN c.check_in_at IS NOT NULL AND c.llamado_a_consulta_at IS NOT NULL
            THEN (julianday(c.llamado_a_consulta_at) - julianday(c.check_in_at)) * 24.0 * 60.0
        END AS espera_min,
        CASE
            WHEN c.consulta_inicio_at IS NOT NULL AND c.consulta_fin_at IS NOT NULL
            THEN (julianday(c.consulta_fin_at) - julianday(c.consulta_inicio_at)) * 24.0 * 60.0
        END AS consulta_min,
        CASE
            WHEN c.consulta_inicio_at IS NOT NULL AND c.inicio IS NOT NULL
            THEN (julianday(c.consulta_inicio_at) - julianday(c.inicio)) * 24.0 * 60.0
        END AS retraso_min
    FROM citas c
    JOIN medicos m ON m.id = c.medico_id
    WHERE c.activo = 1
      AND date(c.inicio) BETWEEN date(?) AND date(?)
)
SELECT
    medico_id,
    medico_nombre,
    COUNT(1) AS total_citas,
    AVG(CASE WHEN consulta_min IS NOT NULL AND consulta_min >= 0 THEN consulta_min END) AS consulta_media_min,
    AVG(CASE WHEN espera_min IS NOT NULL AND espera_min >= 0 THEN espera_min END) AS espera_media_min,
    AVG(CASE WHEN retraso_min IS NOT NULL AND retraso_min >= 0 THEN retraso_min END) AS retraso_media_min,
    (SUM(CASE WHEN estado = 'NO_PRESENTADO' THEN 1 ELSE 0 END) * 100.0) / COUNT(1) AS no_presentado_pct
FROM base
GROUP BY medico_id, medico_nombre
ORDER BY medico_nombre ASC
"""


@dataclass(frozen=True, slots=True)
class KpiDiaRow:
    fecha: str
    total_citas: int
    total_con_checkin: int
    total_validas_espera: int
    espera_media_min: float | None
    total_validas_consulta: int
    consulta_media_min: float | None
    total_validas_total_clinica: int
    total_clinica_media_min: float | None
    total_validas_retraso: int
    retraso_media_min: float | None
    descartados: int


@dataclass(frozen=True, slots=True)
class KpiMedicoRow:
    medico_id: int
    medico_nombre: str
    total_citas: int
    consulta_media_min: float | None
    espera_media_min: float | None
    retraso_media_min: float | None
    no_presentado_pct: float


class MetricasOperativasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def kpis_por_dia(self, desde: date, hasta: date) -> list[KpiDiaRow]:
        rows = self._run_query(_SQL_KPIS_POR_DIA, desde, hasta)
        return [self._map_dia(row) for row in rows]

    def kpis_por_medico(self, desde: date, hasta: date) -> list[KpiMedicoRow]:
        rows = self._run_query(_SQL_KPIS_POR_MEDICO, desde, hasta)
        return [self._map_medico(row) for row in rows]

    def _run_query(self, sql: str, desde: date, hasta: date) -> list[sqlite3.Row]:
        return self._con.execute(sql, (desde.isoformat(), hasta.isoformat())).fetchall()

    @staticmethod
    def _map_dia(row: sqlite3.Row) -> KpiDiaRow:
        return KpiDiaRow(
            fecha=str(row["fecha"]),
            total_citas=int(row["total_citas"] or 0),
            total_con_checkin=int(row["total_con_checkin"] or 0),
            total_validas_espera=int(row["total_validas_espera"] or 0),
            espera_media_min=_float_nullable(row["espera_media_min"]),
            total_validas_consulta=int(row["total_validas_consulta"] or 0),
            consulta_media_min=_float_nullable(row["consulta_media_min"]),
            total_validas_total_clinica=int(row["total_validas_total_clinica"] or 0),
            total_clinica_media_min=_float_nullable(row["total_clinica_media_min"]),
            total_validas_retraso=int(row["total_validas_retraso"] or 0),
            retraso_media_min=_float_nullable(row["retraso_media_min"]),
            descartados=int(row["descartados"] or 0),
        )

    @staticmethod
    def _map_medico(row: sqlite3.Row) -> KpiMedicoRow:
        return KpiMedicoRow(
            medico_id=int(row["medico_id"]),
            medico_nombre=str(row["medico_nombre"]),
            total_citas=int(row["total_citas"] or 0),
            consulta_media_min=_float_nullable(row["consulta_media_min"]),
            espera_media_min=_float_nullable(row["espera_media_min"]),
            retraso_media_min=_float_nullable(row["retraso_media_min"]),
            no_presentado_pct=float(row["no_presentado_pct"] or 0.0),
        )


def _float_nullable(value: object) -> float | None:
    if value is None:
        return None
    return float(value)

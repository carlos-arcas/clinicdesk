from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

_ESTADOS_CERRADOS = ("REALIZADA",)
_ESTADOS_PROXIMOS = ("PROGRAMADA", "CONFIRMADA", "EN_CURSO")


@dataclass(frozen=True, slots=True)
class FilaEntrenamientoDuracion:
    medico_id: int
    tipo_cita: str | None
    duracion_min: float


@dataclass(frozen=True, slots=True)
class FilaEntrenamientoEspera:
    medico_id: int
    franja_hora: str
    dia_semana: int
    espera_min: float


@dataclass(frozen=True, slots=True)
class FilaCitaOperativa:
    cita_id: int
    medico_id: int
    tipo_cita: str | None
    franja_hora: str
    dia_semana: int


@dataclass(frozen=True, slots=True)
class FilaCitaProximaDetalle:
    cita_id: int
    fecha: str
    hora: str
    paciente: str
    medico: str


class PrediccionOperativaQueries:
    def __init__(self, proveedor: ProveedorConexionSqlitePorHilo | sqlite3.Connection) -> None:
        self._proveedor = proveedor

    def _con(self) -> sqlite3.Connection:
        return self._proveedor if isinstance(self._proveedor, sqlite3.Connection) else self._proveedor.obtener()

    def obtener_dataset_duracion(self, desde: str, hasta: str) -> list[FilaEntrenamientoDuracion]:
        rows = self._con().execute(
            """
            SELECT c.medico_id, c.tipo_cita,
                   (julianday(c.consulta_fin_at) - julianday(c.consulta_inicio_at)) * 24.0 * 60.0 AS duracion_min
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?)
              AND datetime(c.inicio) BETWEEN datetime(?) AND datetime(?)
              AND c.consulta_inicio_at IS NOT NULL
              AND c.consulta_fin_at IS NOT NULL
              AND (julianday(c.consulta_fin_at) - julianday(c.consulta_inicio_at)) >= 0
            """,
            (_ESTADOS_CERRADOS[0], desde, hasta),
        ).fetchall()
        return [FilaEntrenamientoDuracion(int(r["medico_id"]), r["tipo_cita"], float(r["duracion_min"])) for r in rows]

    def obtener_dataset_espera(self, desde: str, hasta: str) -> list[FilaEntrenamientoEspera]:
        rows = self._con().execute(
            """
            SELECT c.medico_id,
                   CASE
                     WHEN CAST(strftime('%H', c.inicio) AS INTEGER) < 12 THEN '08-12'
                     WHEN CAST(strftime('%H', c.inicio) AS INTEGER) < 16 THEN '12-16'
                     ELSE '16-20'
                   END AS franja_hora,
                   CAST(strftime('%w', c.inicio) AS INTEGER) AS dia_semana,
                   (julianday(c.llamado_a_consulta_at) - julianday(c.check_in_at)) * 24.0 * 60.0 AS espera_min
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?)
              AND datetime(c.inicio) BETWEEN datetime(?) AND datetime(?)
              AND c.check_in_at IS NOT NULL
              AND c.llamado_a_consulta_at IS NOT NULL
              AND (julianday(c.llamado_a_consulta_at) - julianday(c.check_in_at)) >= 0
            """,
            (_ESTADOS_CERRADOS[0], desde, hasta),
        ).fetchall()
        return [FilaEntrenamientoEspera(int(r["medico_id"]), str(r["franja_hora"]), int(r["dia_semana"]), float(r["espera_min"])) for r in rows]

    def obtener_proximas_citas_para_prediccion(self, desde: str, hasta: str) -> list[FilaCitaOperativa]:
        rows = self._con().execute(
            """
            SELECT c.id AS cita_id, c.medico_id, c.tipo_cita,
                   CASE
                     WHEN CAST(strftime('%H', c.inicio) AS INTEGER) < 12 THEN '08-12'
                     WHEN CAST(strftime('%H', c.inicio) AS INTEGER) < 16 THEN '12-16'
                     ELSE '16-20'
                   END AS franja_hora,
                   CAST(strftime('%w', c.inicio) AS INTEGER) AS dia_semana
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND datetime(c.inicio) BETWEEN datetime(?) AND datetime(?)
            ORDER BY datetime(c.inicio) ASC
            """,
            (*_ESTADOS_PROXIMOS, desde, hasta),
        ).fetchall()
        return [FilaCitaOperativa(int(r["cita_id"]), int(r["medico_id"]), r["tipo_cita"], str(r["franja_hora"]), int(r["dia_semana"])) for r in rows]

    def obtener_proximas_citas_detalle(self, desde: str, hasta: str, limite: int) -> list[FilaCitaProximaDetalle]:
        rows = self._con().execute(
            """
            SELECT c.id AS cita_id,
                   date(c.inicio) AS fecha,
                   time(c.inicio) AS hora,
                   (p.nombre || ' ' || p.apellidos) AS paciente,
                   (m.nombre || ' ' || m.apellidos) AS medico
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND datetime(c.inicio) BETWEEN datetime(?) AND datetime(?)
            ORDER BY datetime(c.inicio) ASC
            LIMIT ?
            """,
            (*_ESTADOS_PROXIMOS, desde, hasta, limite),
        ).fetchall()
        return [
            FilaCitaProximaDetalle(
                cita_id=int(r["cita_id"]),
                fecha=str(r["fecha"]),
                hora=str(r["hora"]),
                paciente=str(r["paciente"]),
                medico=str(r["medico"]),
            )
            for r in rows
        ]

    def contar_citas_validas_recientes_duracion(self, dias: int = 90) -> int:
        row = self._con().execute(
            """
            SELECT COUNT(1) AS total FROM citas c
            WHERE c.activo = 1 AND c.estado = 'REALIZADA'
              AND c.consulta_inicio_at IS NOT NULL AND c.consulta_fin_at IS NOT NULL
              AND datetime(c.inicio) >= datetime('now', ?)
            """,
            (f"-{dias} days",),
        ).fetchone()
        return int(row["total"]) if row else 0

    def contar_citas_validas_recientes_espera(self, dias: int = 90) -> int:
        row = self._con().execute(
            """
            SELECT COUNT(1) AS total FROM citas c
            WHERE c.activo = 1 AND c.estado = 'REALIZADA'
              AND c.check_in_at IS NOT NULL AND c.llamado_a_consulta_at IS NOT NULL
              AND datetime(c.inicio) >= datetime('now', ?)
            """,
            (f"-{dias} days",),
        ).fetchone()
        return int(row["total"]) if row else 0

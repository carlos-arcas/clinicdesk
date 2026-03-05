from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from clinicdesk.app.application.usecases.dashboard_gestion_prediccion import CitaGestionHoyDTO
from clinicdesk.app.infrastructure.sqlite.proveedor_conexion_sqlite import ProveedorConexionSqlitePorHilo

_ESTADOS_PROXIMOS = ("PROGRAMADA", "CONFIRMADA", "EN_CURSO")


@dataclass(frozen=True, slots=True)
class FilaCitaHoyGestion:
    cita_id: int
    hora: str
    paciente_nombre: str
    medico_nombre: str
    paciente_id: int
    medico_id: int
    antelacion_dias: int


class DashboardGestionQueries:
    def __init__(self, proveedor: ProveedorConexionSqlitePorHilo | sqlite3.Connection) -> None:
        self._proveedor = proveedor

    def _con(self) -> sqlite3.Connection:
        return self._proveedor if isinstance(self._proveedor, sqlite3.Connection) else self._proveedor.obtener()

    def listar_citas_hoy_gestion(self, limite: int) -> tuple[CitaGestionHoyDTO, ...]:
        rows = (
            self._con()
            .execute(
                """
            SELECT
                c.id AS cita_id,
                time(c.inicio) AS hora,
                (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
                (m.nombre || ' ' || m.apellidos) AS medico_nombre,
                c.paciente_id,
                c.medico_id,
                CAST(julianday(substr(c.inicio, 1, 10)) - julianday('now') AS INTEGER) AS antelacion_dias
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.activo = 1
              AND c.estado IN (?, ?, ?)
              AND datetime(c.inicio) >= datetime('now', 'start of day')
              AND datetime(c.inicio) < datetime('now', 'start of day', '+1 day')
            ORDER BY datetime(c.inicio) ASC
            LIMIT ?
            """,
                (*_ESTADOS_PROXIMOS, limite),
            )
            .fetchall()
        )
        return tuple(
            CitaGestionHoyDTO(
                cita_id=int(row["cita_id"]),
                hora=str(row["hora"]),
                paciente_nombre=str(row["paciente_nombre"]),
                medico_nombre=str(row["medico_nombre"]),
                paciente_id=int(row["paciente_id"]),
                medico_id=int(row["medico_id"]),
                antelacion_dias=max(0, int(row["antelacion_dias"] or 0)),
            )
            for row in rows
        )

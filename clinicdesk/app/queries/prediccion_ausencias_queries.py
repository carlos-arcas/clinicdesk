from __future__ import annotations

from dataclasses import dataclass
import sqlite3


_ESTADOS_VALIDOS = ("REALIZADA", "NO_PRESENTADO")


@dataclass(frozen=True, slots=True)
class FilaEntrenamientoPrediccion:
    cita_id: int
    paciente_id: int
    estado: str
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class FilaCitaProximaPrediccion:
    cita_id: int
    fecha: str
    hora: str
    paciente: str
    medico: str
    paciente_id: int
    dias_antelacion: int


class PrediccionAusenciasQueries:
    """Consultas de lectura para entrenamiento y previsualización de ausencias."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def contar_citas_validas(self) -> int:
        row = self._con.execute(
            """
            SELECT COUNT(1) AS total
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?)
            """,
            _ESTADOS_VALIDOS,
        ).fetchone()
        return int(row["total"]) if row else 0

    def obtener_dataset_entrenamiento(self) -> list[FilaEntrenamientoPrediccion]:
        rows = self._con.execute(
            """
            SELECT
                c.id AS cita_id,
                c.paciente_id,
                c.estado,
                CAST(
                    julianday(substr(c.inicio, 1, 10)) -
                    julianday(COALESCE(substr(c.override_fecha_hora, 1, 10), substr(c.inicio, 1, 10)))
                    AS INTEGER
                ) AS dias_antelacion
            FROM citas c
            WHERE c.activo = 1
              AND c.estado IN (?, ?)
            ORDER BY c.inicio
            """,
            _ESTADOS_VALIDOS,
        ).fetchall()
        return [
            FilaEntrenamientoPrediccion(
                cita_id=int(r["cita_id"]),
                paciente_id=int(r["paciente_id"]),
                estado=str(r["estado"]),
                dias_antelacion=max(0, int(r["dias_antelacion"] or 0)),
            )
            for r in rows
        ]

    def listar_proximas_citas(self, limite: int = 30) -> list[FilaCitaProximaPrediccion]:
        rows = self._con.execute(
            """
            SELECT
                c.id AS cita_id,
                date(c.inicio) AS fecha,
                time(c.inicio) AS hora,
                (p.nombre || ' ' || p.apellidos) AS paciente,
                (m.nombre || ' ' || m.apellidos) AS medico,
                c.paciente_id,
                CAST(
                    julianday(substr(c.inicio, 1, 10)) -
                    julianday('now')
                    AS INTEGER
                ) AS dias_antelacion
            FROM citas c
            JOIN pacientes p ON p.id = c.paciente_id
            JOIN medicos m ON m.id = c.medico_id
            WHERE c.activo = 1
              AND datetime(c.inicio) >= datetime('now')
              AND c.estado IN ('PROGRAMADA', 'CONFIRMADA', 'EN_CURSO')
            ORDER BY c.inicio
            LIMIT ?
            """,
            (limite,),
        ).fetchall()
        return [
            FilaCitaProximaPrediccion(
                cita_id=int(r["cita_id"]),
                fecha=str(r["fecha"]),
                hora=str(r["hora"]),
                paciente=str(r["paciente"]),
                medico=str(r["medico"]),
                paciente_id=int(r["paciente_id"]),
                dias_antelacion=max(0, int(r["dias_antelacion"] or 0)),
            )
            for r in rows
        ]

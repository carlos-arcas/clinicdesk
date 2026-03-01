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


@dataclass(frozen=True, slots=True)
class FilaCitaRiesgoAgenda:
    cita_id: int
    paciente_id: int
    dias_antelacion: int


@dataclass(frozen=True, slots=True)
class ResumenHistorialPaciente:
    paciente_id: int
    citas_realizadas: int
    citas_no_presentadas: int


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

    def obtener_cita_para_explicacion(self, cita_id: int) -> FilaCitaRiesgoAgenda | None:
        row = self._con.execute(
            """
            SELECT
                c.id AS cita_id,
                c.paciente_id,
                CAST(
                    julianday(substr(c.inicio, 1, 10)) -
                    julianday('now')
                    AS INTEGER
                ) AS dias_antelacion
            FROM citas c
            WHERE c.id = ?
              AND c.activo = 1
            """,
            (cita_id,),
        ).fetchone()
        if row is None:
            return None
        return FilaCitaRiesgoAgenda(
            cita_id=int(row["cita_id"]),
            paciente_id=int(row["paciente_id"]),
            dias_antelacion=max(0, int(row["dias_antelacion"] or 0)),
        )

    def obtener_resumen_historial_paciente(self, paciente_id: int) -> ResumenHistorialPaciente:
        row = self._con.execute(
            """
            SELECT
                c.paciente_id,
                SUM(CASE WHEN c.estado = 'REALIZADA' THEN 1 ELSE 0 END) AS citas_realizadas,
                SUM(CASE WHEN c.estado = 'NO_PRESENTADO' THEN 1 ELSE 0 END) AS citas_no_presentadas
            FROM citas c
            WHERE c.activo = 1
              AND c.paciente_id = ?
              AND c.estado IN ('REALIZADA', 'NO_PRESENTADO')
            GROUP BY c.paciente_id
            """,
            (paciente_id,),
        ).fetchone()
        if row is None:
            return ResumenHistorialPaciente(paciente_id=paciente_id, citas_realizadas=0, citas_no_presentadas=0)
        return ResumenHistorialPaciente(
            paciente_id=int(row["paciente_id"]),
            citas_realizadas=int(row["citas_realizadas"] or 0),
            citas_no_presentadas=int(row["citas_no_presentadas"] or 0),
        )

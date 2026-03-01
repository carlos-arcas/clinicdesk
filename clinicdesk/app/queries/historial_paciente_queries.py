from __future__ import annotations

from dataclasses import dataclass
from typing import List

import logging
import sqlite3


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CitaHistorialRow:
    id: int
    fecha: str
    hora_inicio: str
    hora_fin: str
    medico: str
    estado: str
    resumen: str
    tiene_incidencias: bool


@dataclass(frozen=True, slots=True)
class IncidenciaCitaRow:
    id: int
    fecha_hora: str
    estado: str
    resumen: str


@dataclass(frozen=True, slots=True)
class DetalleCitaRow:
    id: int
    fecha: str
    hora_inicio: str
    hora_fin: str
    estado: str
    sala: str
    medico: str
    paciente: str
    informe: str
    total_incidencias: int
    incidencias: tuple[IncidenciaCitaRow, ...]


class HistorialPacienteQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def listar_citas_por_paciente(self, paciente_id: int, *, limite: int = 200) -> List[CitaHistorialRow]:
        if paciente_id <= 0:
            return []
        try:
            rows = self._connection.execute(self._sql(), (paciente_id, int(limite))).fetchall()
        except sqlite3.Error as exc:
            logger.error("historial_paciente_listar_citas_failed", extra={"paciente_id": paciente_id, "error": str(exc)})
            return []
        return [self._map_row(row) for row in rows]

    def obtener_detalle_cita(self, cita_id: int, *, limite_incidencias: int = 3) -> DetalleCitaRow | None:
        if cita_id <= 0:
            return None
        try:
            row = self._connection.execute(self._sql_detalle_cita(), (cita_id,)).fetchone()
            if row is None:
                return None
            incidencias, total = self._consultar_incidencias(cita_id, limite_incidencias)
        except sqlite3.Error as exc:
            logger.error("historial_paciente_detalle_cita_failed", extra={"cita_id": cita_id, "error": str(exc)})
            return None
        return self._map_detalle_row(row, incidencias, total)

    @staticmethod
    def _sql() -> str:
        return (
            "SELECT c.id AS id, "
            "date(c.inicio) AS fecha, "
            "time(c.inicio) AS hora_inicio, "
            "time(c.fin) AS hora_fin, "
            "(m.nombre || ' ' || m.apellidos) AS medico, "
            "c.estado AS estado, "
            "c.notas AS resumen, "
            "CASE WHEN EXISTS ("
            "SELECT 1 FROM incidencias i WHERE i.cita_id = c.id AND i.activo = 1"
            ") THEN 1 ELSE 0 END AS tiene_incidencias "
            "FROM citas c "
            "JOIN medicos m ON m.id = c.medico_id "
            "WHERE c.activo = 1 AND c.paciente_id = ? "
            "ORDER BY c.inicio DESC "
            "LIMIT ?"
        )

    @staticmethod
    def _sql_detalle_cita() -> str:
        return (
            "SELECT c.id AS id, "
            "date(c.inicio) AS fecha, "
            "time(c.inicio) AS hora_inicio, "
            "time(c.fin) AS hora_fin, "
            "c.estado AS estado, "
            "s.nombre AS sala, "
            "(m.nombre || ' ' || m.apellidos) AS medico, "
            "(p.nombre || ' ' || p.apellidos) AS paciente, "
            "coalesce(c.notas, '') AS informe "
            "FROM citas c "
            "JOIN medicos m ON m.id = c.medico_id "
            "JOIN pacientes p ON p.id = c.paciente_id "
            "JOIN salas s ON s.id = c.sala_id "
            "WHERE c.id = ? AND c.activo = 1"
        )

    def _consultar_incidencias(self, cita_id: int, limite: int) -> tuple[tuple[IncidenciaCitaRow, ...], int]:
        rows = self._connection.execute(
            (
                "SELECT i.id AS id, "
                "i.fecha_hora AS fecha_hora, "
                "i.estado AS estado, "
                "i.descripcion AS resumen, "
                "(SELECT count(*) FROM incidencias x WHERE x.cita_id = ? AND x.activo = 1) AS total_incidencias "
                "FROM incidencias i "
                "WHERE i.cita_id = ? AND i.activo = 1 "
                "ORDER BY i.fecha_hora DESC, i.id DESC "
                "LIMIT ?"
            ),
            (cita_id, cita_id, int(limite)),
        ).fetchall()
        if not rows:
            return (), 0
        incidencias = tuple(self._map_incidencia_row(row) for row in rows)
        return incidencias, int(rows[0]["total_incidencias"] or 0)

    @staticmethod
    def _map_row(row: sqlite3.Row) -> CitaHistorialRow:
        return CitaHistorialRow(
            id=int(row["id"]),
            fecha=row["fecha"] or "",
            hora_inicio=row["hora_inicio"] or "",
            hora_fin=row["hora_fin"] or "",
            medico=row["medico"] or "",
            estado=row["estado"] or "",
            resumen=(row["resumen"] or "").strip(),
            tiene_incidencias=bool(row["tiene_incidencias"]),
        )

    @staticmethod
    def _map_incidencia_row(row: sqlite3.Row) -> IncidenciaCitaRow:
        return IncidenciaCitaRow(
            id=int(row["id"]),
            fecha_hora=row["fecha_hora"] or "",
            estado=row["estado"] or "",
            resumen=(row["resumen"] or "").strip(),
        )

    @staticmethod
    def _map_detalle_row(
        row: sqlite3.Row,
        incidencias: tuple[IncidenciaCitaRow, ...],
        total_incidencias: int,
    ) -> DetalleCitaRow:
        return DetalleCitaRow(
            id=int(row["id"]),
            fecha=row["fecha"] or "",
            hora_inicio=row["hora_inicio"] or "",
            hora_fin=row["hora_fin"] or "",
            estado=row["estado"] or "",
            sala=row["sala"] or "",
            medico=row["medico"] or "",
            paciente=row["paciente"] or "",
            informe=(row["informe"] or "").strip(),
            total_incidencias=total_incidencias,
            incidencias=incidencias,
        )

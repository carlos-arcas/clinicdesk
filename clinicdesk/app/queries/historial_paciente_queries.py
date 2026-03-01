from __future__ import annotations

from dataclasses import dataclass
from typing import List

import logging
import sqlite3


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CitaHistorialRow:
    fecha: str
    hora_inicio: str
    hora_fin: str
    medico: str
    estado: str
    resumen: str
    tiene_incidencias: bool


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

    @staticmethod
    def _sql() -> str:
        return (
            "SELECT date(c.inicio) AS fecha, "
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
    def _map_row(row: sqlite3.Row) -> CitaHistorialRow:
        return CitaHistorialRow(
            fecha=row["fecha"] or "",
            hora_inicio=row["hora_inicio"] or "",
            hora_fin=row["hora_fin"] or "",
            medico=row["medico"] or "",
            estado=row["estado"] or "",
            resumen=(row["resumen"] or "").strip(),
            tiene_incidencias=bool(row["tiene_incidencias"]),
        )

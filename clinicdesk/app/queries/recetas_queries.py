from __future__ import annotations

from dataclasses import dataclass
from typing import List

import logging
import sqlite3


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecetaRow:
    id: int
    fecha: str
    medico: str
    estado: str


@dataclass(frozen=True, slots=True)
class RecetaLineaRow:
    id: int
    medicamento: str
    dosis: str
    cantidad: int
    pendiente: int
    estado: str


class RecetasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list_por_paciente(self, paciente_id: int) -> List[RecetaRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT r.id, r.fecha,
                       (m.nombre || ' ' || m.apellidos) AS medico,
                       r.estado
                FROM recetas r
                JOIN medicos m ON m.id = r.medico_id
                WHERE r.paciente_id = ? AND r.activo = 1
                ORDER BY r.fecha DESC
                """,
                (paciente_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasQueries.list_por_paciente: %s", exc)
            return []

        return [
            RecetaRow(
                id=row["id"],
                fecha=row["fecha"],
                medico=row["medico"],
                estado=row["estado"],
            )
            for row in rows
        ]

    def list_lineas(self, receta_id: int) -> List[RecetaLineaRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT rl.id, med.nombre_comercial AS medicamento,
                       rl.dosis, rl.cantidad, rl.pendiente, rl.estado
                FROM receta_lineas rl
                JOIN medicamentos med ON med.id = rl.medicamento_id
                WHERE rl.receta_id = ? AND rl.activo = 1
                ORDER BY rl.id
                """,
                (receta_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en RecetasQueries.list_lineas: %s", exc)
            return []

        return [
            RecetaLineaRow(
                id=row["id"],
                medicamento=row["medicamento"],
                dosis=row["dosis"],
                cantidad=int(row["cantidad"]),
                pendiente=int(row["pendiente"]),
                estado=row["estado"],
            )
            for row in rows
        ]

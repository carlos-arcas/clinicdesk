from __future__ import annotations

from dataclasses import dataclass
from typing import List

import logging
import sqlite3


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecetaRow:
    id: int
    fecha: str
    medico: str
    estado: str


@dataclass(frozen=True)
class RecetaLineaRow:
    id: int
    medicamento_id: int
    medicamento: str
    dosis: str
    cantidad: int
    pendiente: int
    estado: str


class FarmaciaQueries:
    """Consultas de solo lectura para farmacia listas para la UI."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def recetas_por_paciente(self, paciente_id: int) -> List[RecetaRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT
                    r.id,
                    r.fecha,
                    m.nombre || ' ' || m.apellidos AS medico,
                    r.estado
                FROM recetas r
                JOIN medicos m ON m.id = r.medico_id
                WHERE r.paciente_id = ? AND r.activo = 1
                ORDER BY r.fecha DESC
                """,
                (paciente_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("farmacia_queries_recetas_por_paciente_sql_error", extra={"error": str(exc)})
            return []

        return [
            RecetaRow(
                id=int(row["id"]),
                fecha=row["fecha"],
                medico=row["medico"],
                estado=row["estado"],
            )
            for row in rows
        ]

    def lineas_por_receta(self, receta_id: int) -> List[RecetaLineaRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT
                    rl.id,
                    rl.medicamento_id,
                    med.nombre_comercial AS medicamento,
                    rl.dosis,
                    rl.cantidad,
                    rl.pendiente,
                    rl.estado
                FROM receta_lineas rl
                JOIN medicamentos med ON med.id = rl.medicamento_id
                WHERE rl.receta_id = ? AND rl.activo = 1
                ORDER BY rl.id
                """,
                (receta_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("farmacia_queries_lineas_por_receta_sql_error", extra={"error": str(exc)})
            return []

        return [
            RecetaLineaRow(
                id=int(row["id"]),
                medicamento_id=int(row["medicamento_id"]),
                medicamento=row["medicamento"],
                dosis=row["dosis"],
                cantidad=int(row["cantidad"]),
                pendiente=int(row["pendiente"]),
                estado=row["estado"],
            )
            for row in rows
        ]

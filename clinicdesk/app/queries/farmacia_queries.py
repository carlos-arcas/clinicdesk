from __future__ import annotations

from dataclasses import dataclass
from typing import List

import sqlite3


# =========================
# DTOs para la UI
# =========================

@dataclass(frozen=True)
class RecetaRow:
    id: int
    fecha: str
    medico: str
    estado: str


@dataclass(frozen=True)
class RecetaLineaRow:
    id: int
    medicamento: str
    dosis: str
    cantidad: int
    pendiente: int
    estado: str


# =========================
# Queries
# =========================

class FarmaciaQueries:
    """
    Consultas de SOLO lectura para Farmacia.
    Devuelve datos ya preparados para la UI.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    # -------- Recetas --------

    def recetas_por_paciente(self, paciente_id: int) -> List[RecetaRow]:
        cur = self._conn.execute(
            """
            SELECT
                r.id,
                r.fecha,
                m.nombre || ' ' || m.apellidos AS medico,
                r.estado
            FROM recetas r
            JOIN medicos m ON m.id = r.medico_id
            WHERE r.paciente_id = ?
            ORDER BY r.fecha DESC
            """,
            (paciente_id,),
        )

        return [
            RecetaRow(
                id=row["id"],
                fecha=row["fecha"],
                medico=row["medico"],
                estado=row["estado"],
            )
            for row in cur.fetchall()
        ]

    # -------- Líneas de receta --------

    def lineas_por_receta(self, receta_id: int) -> List[RecetaLineaRow]:
        cur = self._conn.execute(
            """
            SELECT
                rl.id,
                med.nombre_comercial AS medicamento,
                rl.dosis,
                rl.cantidad,
                rl.pendiente,
                rl.estado
            FROM receta_lineas rl
            JOIN medicamentos med ON med.id = rl.medicamento_id
            WHERE rl.receta_id = ?
            ORDER BY rl.id
            """,
            (receta_id,),
        )

        return [
            RecetaLineaRow(
                id=row["id"],
                medicamento=row["medicamento"],
                dosis=row["dosis"],
                cantidad=row["cantidad"],
                pendiente=row["pendiente"],
                estado=row["estado"],
            )
            for row in cur.fetchall()
        ]

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


@dataclass(frozen=True, slots=True)
class RecetaPacienteFlatRow:
    receta_id: int
    receta_fecha: str
    receta_estado: str
    receta_activo: int
    medico_nombre: str
    linea_id: int | None
    medicamento_nombre: str | None
    linea_dosis: str | None
    linea_cantidad: int | None
    linea_pendiente: int | None
    linea_estado: str | None
    linea_duracion_dias: int | None
    linea_activo: int | None


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
        except sqlite3.Error:
            logger.exception("Error SQL en list_por_paciente", extra={"paciente_id": paciente_id})
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
        except sqlite3.Error:
            logger.exception("Error SQL en list_lineas", extra={"receta_id": receta_id})
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

    def list_flat_por_paciente(self, paciente_id: int) -> List[RecetaPacienteFlatRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT
                    r.id AS receta_id,
                    r.fecha AS receta_fecha,
                    r.estado AS receta_estado,
                    r.activo AS receta_activo,
                    (m.nombre || ' ' || m.apellidos) AS medico_nombre,
                    rl.id AS linea_id,
                    COALESCE(med.nombre_comercial, med.nombre_compuesto) AS medicamento_nombre,
                    rl.dosis AS linea_dosis,
                    rl.cantidad AS linea_cantidad,
                    rl.pendiente AS linea_pendiente,
                    rl.estado AS linea_estado,
                    rl.duracion_dias AS linea_duracion_dias,
                    rl.activo AS linea_activo
                FROM recetas r
                JOIN medicos m ON m.id = r.medico_id
                LEFT JOIN receta_lineas rl ON rl.receta_id = r.id AND rl.activo = 1
                LEFT JOIN medicamentos med ON med.id = rl.medicamento_id
                WHERE r.paciente_id = ? AND r.activo = 1
                ORDER BY r.fecha DESC, r.id DESC, rl.id ASC
                """,
                (paciente_id,),
            ).fetchall()
        except sqlite3.Error:
            logger.exception("Error SQL en list_flat_por_paciente", extra={"paciente_id": paciente_id})
            return []

        return [
            RecetaPacienteFlatRow(
                receta_id=row["receta_id"],
                receta_fecha=row["receta_fecha"],
                receta_estado=row["receta_estado"],
                receta_activo=int(row["receta_activo"]),
                medico_nombre=row["medico_nombre"],
                linea_id=row["linea_id"],
                medicamento_nombre=row["medicamento_nombre"],
                linea_dosis=row["linea_dosis"],
                linea_cantidad=int(row["linea_cantidad"]) if row["linea_cantidad"] is not None else None,
                linea_pendiente=int(row["linea_pendiente"]) if row["linea_pendiente"] is not None else None,
                linea_estado=row["linea_estado"],
                linea_duracion_dias=(
                    int(row["linea_duracion_dias"]) if row["linea_duracion_dias"] is not None else None
                ),
                linea_activo=int(row["linea_activo"]) if row["linea_activo"] is not None else None,
            )
            for row in rows
        ]

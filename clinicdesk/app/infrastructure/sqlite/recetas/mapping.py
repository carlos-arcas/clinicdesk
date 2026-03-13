from __future__ import annotations

from datetime import datetime
import sqlite3

from clinicdesk.app.domain.modelos import Receta, RecetaLinea


def row_to_receta(row: sqlite3.Row) -> Receta:
    return Receta(
        id=row["id"],
        paciente_id=row["paciente_id"],
        medico_id=row["medico_id"],
        fecha=datetime.fromisoformat(row["fecha"]),
        observaciones=row["observaciones"],
    )


def row_to_linea(row: sqlite3.Row) -> RecetaLinea:
    return RecetaLinea(
        id=row["id"],
        receta_id=row["receta_id"],
        medicamento_id=row["medicamento_id"],
        dosis=row["dosis"],
        duracion_dias=row["duracion_dias"],
        instrucciones=row["instrucciones"],
    )

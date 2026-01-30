from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class DispensacionRow:
    id: int
    fecha_hora: str
    paciente: str
    personal: str
    medicamento: str
    cantidad: int
    receta_id: int
    incidencia: bool


class DispensacionesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def list(
        self,
        *,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        paciente_texto: Optional[str] = None,
        personal_texto: Optional[str] = None,
        medicamento_texto: Optional[str] = None,
        limit: int = 500,
    ) -> List[DispensacionRow]:
        clauses = []
        params: List[object] = []

        if fecha_desde:
            clauses.append("d.fecha_hora >= ?")
            params.append(f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            clauses.append("d.fecha_hora <= ?")
            params.append(f"{fecha_hasta} 23:59:59")
        if paciente_texto:
            like = f"%{paciente_texto}%"
            clauses.append(
                "(p.nombre LIKE ? OR p.apellidos LIKE ? OR p.documento LIKE ? OR p.telefono LIKE ?)"
            )
            params.extend([like, like, like, like])
        if personal_texto:
            like = f"%{personal_texto}%"
            clauses.append(
                "(per.nombre LIKE ? OR per.apellidos LIKE ? OR per.documento LIKE ? OR per.telefono LIKE ? OR per.puesto LIKE ?)"
            )
            params.extend([like, like, like, like, like])
        if medicamento_texto:
            like = f"%{medicamento_texto}%"
            clauses.append("(m.nombre_comercial LIKE ? OR m.nombre_compuesto LIKE ?)")
            params.extend([like, like])

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        rows = self._conn.execute(
            f"""
            SELECT d.id, d.fecha_hora,
                   (p.nombre || ' ' || p.apellidos) AS paciente,
                   (per.nombre || ' ' || per.apellidos) AS personal,
                   m.nombre_comercial AS medicamento,
                   d.cantidad, d.receta_id, d.incidencia
            FROM dispensaciones d
            JOIN recetas r ON r.id = d.receta_id
            JOIN pacientes p ON p.id = r.paciente_id
            JOIN personal per ON per.id = d.personal_id
            JOIN medicamentos m ON m.id = d.medicamento_id
            {where_sql}
            ORDER BY d.fecha_hora DESC
            LIMIT ?
            """,
            (*params, int(limit)),
        ).fetchall()

        return [
            DispensacionRow(
                id=row["id"],
                fecha_hora=row["fecha_hora"],
                paciente=row["paciente"],
                personal=row["personal"],
                medicamento=row["medicamento"],
                cantidad=int(row["cantidad"]),
                receta_id=row["receta_id"],
                incidencia=bool(row["incidencia"]),
            )
            for row in rows
        ]

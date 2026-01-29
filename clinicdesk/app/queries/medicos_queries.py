from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class MedicoRow:
    id: int
    documento: str
    nombre_completo: str
    telefono: str
    especialidad: str
    activo: bool


class MedicosQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        especialidad: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[MedicoRow]:
        clauses = []
        params: List[object] = []

        if texto:
            like = f"%{texto}%"
            clauses.append(
                "(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ? OR telefono LIKE ? OR num_colegiado LIKE ?)"
            )
            params.extend([like, like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses.append(
                    "REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ?"
                )
                params.append(f"%{cleaned}%")

        if especialidad:
            clauses.append("especialidad = ?")
            params.append(especialidad)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, especialidad, activo FROM medicos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

        rows = self._conn.execute(sql, params).fetchall()
        return [
            MedicoRow(
                id=row["id"],
                documento=row["documento"],
                nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
                telefono=row["telefono"] or "",
                especialidad=row["especialidad"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

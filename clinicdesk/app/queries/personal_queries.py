from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class PersonalRow:
    id: int
    documento: str
    nombre_completo: str
    telefono: str
    puesto: str
    activo: bool


class PersonalQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[PersonalRow]:
        clauses = []
        params: List[object] = []

        if texto:
            like = f"%{texto}%"
            clauses.append(
                "(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ? OR telefono LIKE ? OR puesto LIKE ?)"
            )
            params.extend([like, like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses.append(
                    "REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ?"
                )
                params.append(f"%{cleaned}%")

        if puesto:
            clauses.append("puesto = ?")
            params.append(puesto)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, puesto, activo FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

        rows = self._conn.execute(sql, params).fetchall()
        return [
            PersonalRow(
                id=row["id"],
                documento=row["documento"],
                nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
                telefono=row["telefono"] or "",
                puesto=row["puesto"],
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class SalaRow:
    id: int
    nombre: str
    tipo: str
    ubicacion: str
    activa: bool


class SalasQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo: Optional[str] = None,
        activa: Optional[bool] = True,
        limit: int = 500,
    ) -> List[SalaRow]:
        clauses = []
        params: List[object] = []

        if texto:
            like = f"%{texto}%"
            clauses.append("(nombre LIKE ? OR ubicacion LIKE ?)")
            params.extend([like, like])

        if tipo:
            clauses.append("tipo = ?")
            params.append(tipo)

        if activa is not None:
            clauses.append("activa = ?")
            params.append(int(activa))

        sql = "SELECT id, nombre, tipo, ubicacion, activa FROM salas"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre LIMIT ?"
        params.append(int(limit))

        rows = self._conn.execute(sql, params).fetchall()
        return [
            SalaRow(
                id=row["id"],
                nombre=row["nombre"],
                tipo=row["tipo"],
                ubicacion=row["ubicacion"] or "",
                activa=bool(row["activa"]),
            )
            for row in rows
        ]

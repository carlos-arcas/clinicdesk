from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class PacienteRow:
    id: int
    documento: str
    nombre_completo: str
    telefono: str
    activo: bool


class PacientesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[PacienteRow]:
        clauses = []
        params: List[object] = []

        if texto:
            like = f"%{texto}%"
            clauses.append(
                "(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ? OR telefono LIKE ?)"
            )
            params.extend([like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses.append(
                    "REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ?"
                )
                params.append(f"%{cleaned}%")

        if tipo_documento:
            clauses.append("tipo_documento = ?")
            params.append(tipo_documento)

        if documento:
            clauses.append("documento = ?")
            params.append(documento)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, activo FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

        rows = self._conn.execute(sql, params).fetchall()
        return [
            PacienteRow(
                id=row["id"],
                documento=row["documento"],
                nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
                telefono=row["telefono"] or "",
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

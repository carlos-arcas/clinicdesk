from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class MaterialRow:
    id: int
    nombre: str
    stock: int
    fungible: bool
    activo: bool


@dataclass(frozen=True, slots=True)
class MovimientoMaterialRow:
    id: int
    fecha_hora: str
    tipo: str
    cantidad: int
    personal: str
    motivo: str


class MaterialesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[MaterialRow]:
        clauses = []
        params: List[object] = []

        if texto:
            like = f"%{texto}%"
            clauses.append("nombre LIKE ?")
            params.append(like)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, nombre, fungible, cantidad_en_almacen, activo FROM materiales"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre LIMIT ?"
        params.append(int(limit))

        rows = self._conn.execute(sql, params).fetchall()
        return [
            MaterialRow(
                id=row["id"],
                nombre=row["nombre"],
                stock=int(row["cantidad_en_almacen"]),
                fungible=bool(row["fungible"]),
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def list_movimientos(self, material_id: int, *, limit: int = 200) -> List[MovimientoMaterialRow]:
        rows = self._conn.execute(
            """
            SELECT mm.id, mm.fecha_hora, mm.tipo, mm.cantidad,
                   (p.nombre || ' ' || p.apellidos) AS personal,
                   mm.motivo
            FROM movimientos_materiales mm
            LEFT JOIN personal p ON p.id = mm.personal_id
            WHERE mm.material_id = ?
            ORDER BY mm.fecha_hora DESC
            LIMIT ?
            """,
            (material_id, int(limit)),
        ).fetchall()

        return [
            MovimientoMaterialRow(
                id=row["id"],
                fecha_hora=row["fecha_hora"],
                tipo=row["tipo"],
                cantidad=int(row["cantidad"]),
                personal=row["personal"] or "",
                motivo=row["motivo"] or "",
            )
            for row in rows
        ]

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import has_search_values, like_value, normalize_search_text


logger = logging.getLogger(__name__)


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
        texto = normalize_search_text(texto)

        if not has_search_values(texto):
            logger.info("Materiales search skipped (filtros vacíos).")
            return []

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append("nombre LIKE ? COLLATE NOCASE")
            params.append(like)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, nombre, fungible, cantidad_en_almacen, activo FROM materiales"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MaterialesQueries.search: %s", exc)
            return []
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
        try:
            rows = self._conn.execute(
                """
                SELECT mm.id, mm.fecha_hora, mm.tipo, mm.cantidad,
                       (p.nombre || ' ' || p.apellidos) AS personal,
                       mm.motivo
                FROM movimientos_materiales mm
                LEFT JOIN personal p ON p.id = mm.personal_id
                WHERE mm.material_id = ? AND mm.activo = 1
                ORDER BY mm.fecha_hora DESC
                LIMIT ?
                """,
                (material_id, int(limit)),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MaterialesQueries.list_movimientos: %s", exc)
            return []

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

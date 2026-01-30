from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


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

    def list_all(
        self,
        *,
        activa: Optional[bool] = True,
        limit: int = 500,
    ) -> List[SalaRow]:
        clauses = []
        params: List[object] = []

        if activa is not None:
            clauses.append("activa = ?")
            params.append(int(activa))

        sql = "SELECT id, nombre, tipo, ubicacion, activa FROM salas"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en SalasQueries.list_all: %s", exc)
            return []
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

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo: Optional[str] = None,
        activa: Optional[bool] = True,
        limit: int = 500,
    ) -> List[SalaRow]:
        texto = normalize_search_text(texto)
        tipo = normalize_search_text(tipo)

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append("(nombre LIKE ? COLLATE NOCASE OR ubicacion LIKE ? COLLATE NOCASE)")
            params.extend([like, like])

        if tipo:
            clauses.append("tipo LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo))

        if activa is not None:
            clauses.append("activa = ?")
            params.append(int(activa))

        sql = "SELECT id, nombre, tipo, ubicacion, activa FROM salas"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en SalasQueries.search: %s", exc)
            return []
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

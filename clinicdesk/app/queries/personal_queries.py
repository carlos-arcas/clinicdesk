from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


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

    def list_all(
        self,
        *,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[PersonalRow]:
        clauses = []
        params: List[object] = []

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, puesto, activo FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre, id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))
        if offset > 0:
            if limit is None:
                sql += " LIMIT -1"
            sql += " OFFSET ?"
            params.append(int(offset))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PersonalQueries.list_all: %s", exc)
            return []
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

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[PersonalRow]:
        texto = normalize_search_text(texto)
        puesto = normalize_search_text(puesto)

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE OR telefono LIKE ? COLLATE NOCASE "
                "OR puesto LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses[-1] = (
                    clauses[-1][:-1]
                    + " OR REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE)"
                )
                params.append(like_value(cleaned))

        if puesto:
            clauses.append("puesto LIKE ? COLLATE NOCASE")
            params.append(like_value(puesto))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, puesto, activo FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre, id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))
        if offset > 0:
            if limit is None:
                sql += " LIMIT -1"
            sql += " OFFSET ?"
            params.append(int(offset))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PersonalQueries.search: %s", exc)
            return []
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

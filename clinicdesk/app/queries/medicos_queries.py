from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


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

    _BASE_SELECT = (
        "SELECT id, documento, nombre, apellidos, telefono, "
        "GROUP_CONCAT(DISTINCT especialidad) AS especialidad, activo "
        "FROM medicos"
    )

    def list_all(
        self,
        *,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[MedicoRow]:
        clauses = []
        params: List[object] = []

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = self._BASE_SELECT
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " GROUP BY id, documento, nombre, apellidos, telefono, activo"
        sql += " ORDER BY apellidos, nombre, id"
        sql, params = self._with_pagination(sql, params, limit=limit, offset=offset)

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicosQueries.list_all: %s", exc)
            return []
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

    def search(
        self,
        *,
        texto: Optional[str] = None,
        especialidad: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[MedicoRow]:
        texto = normalize_search_text(texto)
        especialidad = normalize_search_text(especialidad)

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE OR telefono LIKE ? COLLATE NOCASE "
                "OR num_colegiado LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses[-1] = (
                    clauses[-1][:-1]
                    + " OR REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE)"
                )
                params.append(like_value(cleaned))

        if especialidad:
            clauses.append("especialidad LIKE ? COLLATE NOCASE")
            params.append(like_value(especialidad))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = self._BASE_SELECT
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " GROUP BY id, documento, nombre, apellidos, telefono, activo"
        sql += " ORDER BY apellidos, nombre, id"
        sql, params = self._with_pagination(sql, params, limit=limit, offset=offset)

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicosQueries.search: %s", exc)
            return []
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

    @staticmethod
    def _with_pagination(
        sql: str,
        params: List[object],
        *,
        limit: Optional[int],
        offset: int,
    ) -> tuple[str, List[object]]:
        normalized_offset = max(0, int(offset))
        if limit is not None:
            sql += " LIMIT ?"
            params.append(max(1, int(limit)))
            if normalized_offset:
                sql += " OFFSET ?"
                params.append(normalized_offset)
            return sql, params

        if normalized_offset:
            sql += " LIMIT -1 OFFSET ?"
            params.append(normalized_offset)
        return sql, params

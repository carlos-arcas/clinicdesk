from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text


logger = logging.getLogger(__name__)


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

    def list_all(
        self,
        *,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[PacienteRow]:
        clauses = []
        params: List[object] = []

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, activo FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre, id"
        sql, params = self._with_pagination(sql, params, limit=limit, offset=offset)

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesQueries.list_all: %s", exc)
            return []
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

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[PacienteRow]:
        texto = normalize_search_text(texto)
        documento = normalize_search_text(documento)
        tipo_documento = normalize_search_text(tipo_documento)

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE OR telefono LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                clauses[-1] = (
                    clauses[-1][:-1]
                    + " OR REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE)"
                )
                params.append(like_value(cleaned))

        if tipo_documento:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento))

        if documento:
            clauses.append("documento LIKE ? COLLATE NOCASE")
            params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, activo FROM pacientes"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre, id"
        sql, params = self._with_pagination(sql, params, limit=limit, offset=offset)

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesQueries.search: %s", exc)
            return []
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

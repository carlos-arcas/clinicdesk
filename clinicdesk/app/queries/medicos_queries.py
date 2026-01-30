from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import has_search_values, like_value, normalize_search_text


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

    def search(
        self,
        *,
        texto: Optional[str] = None,
        especialidad: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[MedicoRow]:
        texto = normalize_search_text(texto)
        especialidad = normalize_search_text(especialidad)

        if not has_search_values(texto, especialidad):
            logger.info("Medicos search skipped (filtros vacíos).")
            return []

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
                clauses.append(
                    "REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE"
                )
                params.append(like_value(cleaned))

        if especialidad:
            clauses.append("especialidad LIKE ? COLLATE NOCASE")
            params.append(like_value(especialidad))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, documento, nombre, apellidos, telefono, especialidad, activo FROM medicos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

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

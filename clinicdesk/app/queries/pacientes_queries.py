from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.infrastructure.sqlite.paciente_field_crypto import (
    documento_hash_for_query,
    resolve_field,
    telefono_hash_for_query,
)

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

    def list_all(self, *, activo: Optional[bool] = True, limit: int = 500) -> list[PacienteRow]:
        clauses: list[str] = []
        params: list[object] = []
        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = (
            "SELECT id, documento, documento_enc, nombre, apellidos, telefono, telefono_enc, activo "
            "FROM pacientes"
        )
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesQueries.list_all: %s", exc)
            return []
        return [self._to_row(row) for row in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> list[PacienteRow]:
        texto = normalize_search_text(texto)
        documento = normalize_search_text(documento)
        tipo_documento = normalize_search_text(tipo_documento)

        clauses: list[str] = []
        params: list[object] = []
        if texto:
            like = like_value(texto)
            text_clauses = [
                "nombre LIKE ? COLLATE NOCASE",
                "apellidos LIKE ? COLLATE NOCASE",
                "documento LIKE ? COLLATE NOCASE",
                "telefono LIKE ? COLLATE NOCASE",
            ]
            params.extend([like, like, like, like])

            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                text_clauses.append("REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE")
                params.append(like_value(cleaned))

            doc_hash = documento_hash_for_query(texto)
            tel_hash = telefono_hash_for_query(texto)
            if doc_hash:
                text_clauses.append("documento_hash = ?")
                params.append(doc_hash)
            if tel_hash:
                text_clauses.append("telefono_hash = ?")
                params.append(tel_hash)
            clauses.append("(" + " OR ".join(text_clauses) + ")")

        if tipo_documento:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento))

        if documento:
            doc_hash = documento_hash_for_query(documento)
            if doc_hash:
                clauses.append("(documento_hash = ? OR documento LIKE ? COLLATE NOCASE)")
                params.extend([doc_hash, like_value(documento)])
            else:
                clauses.append("documento LIKE ? COLLATE NOCASE")
                params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = (
            "SELECT id, documento, documento_enc, nombre, apellidos, telefono, telefono_enc, activo "
            "FROM pacientes"
        )
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PacientesQueries.search: %s", exc)
            return []
        return [self._to_row(row) for row in rows]

    @staticmethod
    def _to_row(row: sqlite3.Row) -> PacienteRow:
        return PacienteRow(
            id=row["id"],
            documento=resolve_field(legacy=row["documento"], encrypted=row["documento_enc"]) or "",
            nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
            telefono=resolve_field(legacy=row["telefono"], encrypted=row["telefono_enc"]) or "",
            activo=bool(row["activo"]),
        )

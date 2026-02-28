from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.infrastructure.sqlite.medicos_field_protection import MedicosFieldProtection


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
        self._field_protection = MedicosFieldProtection(connection)
        self._columns = _table_columns(connection)

    def _base_select_sql(self) -> str:
        doc_enc = "documento_enc" if "documento_enc" in self._columns else "NULL AS documento_enc"
        doc_hash = "documento_hash" if "documento_hash" in self._columns else "NULL AS documento_hash"
        tel_enc = "telefono_enc" if "telefono_enc" in self._columns else "NULL AS telefono_enc"
        return (
            "SELECT id, documento, "
            f"{doc_enc}, {doc_hash}, "
            "nombre, apellidos, telefono, "
            f"{tel_enc}, GROUP_CONCAT(DISTINCT especialidad) AS especialidad, activo "
            "FROM medicos"
        )

    def _build_texto_clause(self, texto: Optional[str]) -> tuple[Optional[str], List[object]]:
        if not texto:
            return None, []
        like = like_value(texto)
        conditions = [
            "nombre LIKE ? COLLATE NOCASE",
            "apellidos LIKE ? COLLATE NOCASE",
            "num_colegiado LIKE ? COLLATE NOCASE",
        ]
        params: List[object] = [like, like, like]
        if not self._field_protection.enabled:
            conditions.extend(["documento LIKE ? COLLATE NOCASE", "telefono LIKE ? COLLATE NOCASE"])
            params.extend([like, like])
            cleaned = texto.replace(" ", "").replace("-", "")
            if cleaned:
                conditions.append("REPLACE(REPLACE(telefono, ' ', ''), '-', '') LIKE ? COLLATE NOCASE")
                params.append(like_value(cleaned))
        return "(" + " OR ".join(conditions) + ")", params

    @staticmethod
    def _build_especialidad_clause(especialidad: Optional[str]) -> tuple[Optional[str], List[object]]:
        if not especialidad:
            return None, []
        return "especialidad LIKE ? COLLATE NOCASE", [like_value(especialidad)]

    @staticmethod
    def _build_activo_clause(activo: Optional[bool]) -> tuple[Optional[str], List[object]]:
        if activo is None:
            return None, []
        return "activo = ?", [int(activo)]

    def _build_documento_clause(self, documento: Optional[str]) -> tuple[Optional[str], List[object]]:
        if not documento:
            return None, []
        if self._field_protection.enabled and "documento_hash" in self._columns:
            return "documento_hash = ?", [self._field_protection.hash_for_lookup("documento", documento)]
        return "documento LIKE ? COLLATE NOCASE", [like_value(documento)]

    @staticmethod
    def _build_where(*parts: tuple[Optional[str], List[object]]) -> tuple[str, List[object]]:
        clauses = [clause for clause, _ in parts if clause]
        params = [param for _, values in parts for param in values]
        if not clauses:
            return "", params
        return " WHERE " + " AND ".join(clauses), params

    def list_all(self, *, activo: Optional[bool] = True, limit: Optional[int] = None, offset: int = 0) -> List[MedicoRow]:
        where_sql, params = self._build_where(self._build_activo_clause(activo))
        sql = self._base_select_sql() + where_sql
        sql += " GROUP BY id, documento, documento_enc, documento_hash, nombre, apellidos, telefono, telefono_enc, activo"
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
            logger.error("Error SQL en MedicosQueries.list_all: %s", exc)
            return []
        return [self._to_row(row) for row in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        especialidad: Optional[str] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[MedicoRow]:
        texto = normalize_search_text(texto)
        especialidad = normalize_search_text(especialidad)
        documento = normalize_search_text(documento)
        where_sql, params = self._build_where(
            self._build_texto_clause(texto),
            self._build_especialidad_clause(especialidad),
            self._build_documento_clause(documento),
            self._build_activo_clause(activo),
        )
        sql = self._base_select_sql() + where_sql
        sql += " GROUP BY id, documento, documento_enc, documento_hash, nombre, apellidos, telefono, telefono_enc, activo"
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
            logger.error("Error SQL en MedicosQueries.search: %s", exc)
            return []
        return [self._to_row(row) for row in rows]

    def _to_row(self, row: sqlite3.Row) -> MedicoRow:
        documento = self._field_protection.decode("documento", legacy=row["documento"], encrypted=row["documento_enc"])
        telefono = self._field_protection.decode("telefono", legacy=row["telefono"], encrypted=row["telefono_enc"])
        return MedicoRow(
            id=row["id"],
            documento=documento or "",
            nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
            telefono=telefono or "",
            especialidad=row["especialidad"],
            activo=bool(row["activo"]),
        )


def _table_columns(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("PRAGMA table_info(medicos)").fetchall()
    return {row["name"] for row in rows}

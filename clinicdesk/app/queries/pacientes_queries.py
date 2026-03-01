from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.infrastructure.sqlite.pacientes_field_protection import PacientesFieldProtection


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PacienteRow:
    id: int
    tipo_documento: str
    documento: str
    nombre: str
    apellidos: str
    nombre_completo: str
    telefono: str
    email: str
    fecha_nacimiento: str
    direccion: str
    activo: bool
    num_historia: str
    alergias: str
    observaciones: str


class PacientesQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._field_protection = PacientesFieldProtection(connection)

    def list_all(
        self,
        *,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[PacienteRow]:
        clauses = []
        params: List[object] = []
        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = self._base_select_sql()
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
    ) -> List[PacienteRow]:
        texto = normalize_search_text(texto)
        documento = normalize_search_text(documento)
        tipo_documento = normalize_search_text(tipo_documento)

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            if self._field_protection.enabled:
                clauses.append("(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE)")
                params.extend([like, like])
            else:
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
            if self._field_protection.enabled:
                clauses.append("documento_hash = ?")
                params.append(self._field_protection.hash_for_lookup("documento", documento))
            else:
                clauses.append("documento LIKE ? COLLATE NOCASE")
                params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = self._base_select_sql()
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
    def _base_select_sql() -> str:
        return (
            "SELECT id, tipo_documento, documento, documento_enc, nombre, apellidos, "
            "telefono, telefono_enc, email, email_enc, fecha_nacimiento, direccion, direccion_enc, "
            "activo, num_historia, alergias, observaciones FROM pacientes"
        )

    def _to_row(self, row: sqlite3.Row) -> PacienteRow:
        documento = self._field_protection.decode(
            "documento",
            legacy=row["documento"],
            encrypted=row["documento_enc"],
        )
        telefono = self._field_protection.decode(
            "telefono",
            legacy=row["telefono"],
            encrypted=row["telefono_enc"],
        )
        email = self._field_protection.decode(
            "email",
            legacy=row["email"],
            encrypted=row["email_enc"],
        )
        direccion = self._field_protection.decode(
            "direccion",
            legacy=row["direccion"],
            encrypted=row["direccion_enc"],
        )
        return PacienteRow(
            id=row["id"],
            tipo_documento=row["tipo_documento"],
            documento=documento or "",
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            nombre_completo=f"{row['nombre']} {row['apellidos']}".strip(),
            telefono=telefono or "",
            email=email or "",
            fecha_nacimiento=row["fecha_nacimiento"] or "",
            direccion=direccion or "",
            activo=bool(row["activo"]),
            num_historia=row["num_historia"] or "",
            alergias=row["alergias"] or "",
            observaciones=row["observaciones"] or "",
        )

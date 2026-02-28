# infrastructure/sqlite/repos_personal.py
"""
Repositorio SQLite para Personal.

Responsabilidades:
- CRUD de personal
- Búsquedas con filtros (puesto, activo, texto libre)
- Conversión fila <-> modelo de dominio

No contiene:
- Lógica de cuadrantes
- Lógica de dispensación
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date


logger = logging.getLogger(__name__)


class _PersonalConsultasSqlite:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    def get_by_id(self, personal_id: int) -> Optional[Personal]:
        row = self._con.execute("SELECT * FROM personal WHERE id = ?", (personal_id,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_id_by_documento(
        self,
        tipo_documento: TipoDocumento | str,
        documento: str,
    ) -> Optional[int]:
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = self._con.execute(
            "SELECT id FROM personal WHERE tipo_documento = ? AND documento = ?",
            (tipo, documento),
        ).fetchone()
        return int(row["id"]) if row else None

    def get_id_by_nombre(self, nombre: str, apellidos: Optional[str] = None) -> Optional[int]:
        nombre = normalize_search_text(nombre)
        apellidos = normalize_search_text(apellidos)
        if not nombre:
            return None
        clauses = ["nombre LIKE ? COLLATE NOCASE"]
        params: list[object] = [like_value(nombre)]
        if apellidos:
            clauses.append("apellidos LIKE ? COLLATE NOCASE")
            params.append(like_value(apellidos))
        sql = "SELECT id FROM personal WHERE " + " AND ".join(clauses) + " ORDER BY apellidos, nombre"
        row = self._con.execute(sql, params).fetchone()
        return int(row["id"]) if row else None

    def list_all(self, *, solo_activos: bool = True) -> List[Personal]:
        sql = "SELECT * FROM personal"
        if solo_activos:
            sql += " WHERE activo = 1"
        sql += " ORDER BY apellidos, nombre"
        try:
            rows = self._con.execute(sql).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PersonalRepository.list_all: %s", exc)
            return []
        return [self._row_to_model(row) for row in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Personal]:
        clauses, params = self._build_search_filters(texto, puesto, tipo_documento, documento, activo)
        sql = "SELECT * FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY apellidos, nombre"
        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en PersonalRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def _build_search_filters(
        self,
        texto: Optional[str],
        puesto: Optional[str],
        tipo_documento: Optional[TipoDocumento],
        documento: Optional[str],
        activo: Optional[bool],
    ) -> tuple[list[str], list[object]]:
        texto = normalize_search_text(texto)
        puesto = normalize_search_text(puesto)
        documento = normalize_search_text(documento)
        tipo_documento_value = normalize_search_text(tipo_documento.value if tipo_documento else None)

        clauses: list[str] = []
        params: list[object] = []
        if texto:
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE)"
            )
            like = like_value(texto)
            params.extend([like, like, like])
        if puesto:
            clauses.append("puesto LIKE ? COLLATE NOCASE")
            params.append(like_value(puesto))
        if tipo_documento_value:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento_value))
        if documento:
            clauses.append("documento LIKE ? COLLATE NOCASE")
            params.append(like_value(documento))
        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))
        return clauses, params

    def _row_to_model(self, row: sqlite3.Row) -> Personal:
        return Personal(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=row["documento"],
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=row["telefono"],
            email=row["email"],
            fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
            direccion=row["direccion"],
            activo=bool(row["activo"]),
            puesto=row["puesto"],
            turno=row["turno"],
        )


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class PersonalRepository:
    """Repositorio de acceso a datos para personal."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._consultas = _PersonalConsultasSqlite(connection)

    def create(self, personal: Personal) -> int:
        personal.validar()
        cur = self._con.execute(
            """
            INSERT INTO personal (
                tipo_documento, documento,
                nombre, apellidos,
                telefono, email,
                fecha_nacimiento, direccion,
                activo,
                puesto, turno
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                personal.tipo_documento.value,
                personal.documento,
                personal.nombre,
                personal.apellidos,
                personal.telefono,
                personal.email,
                format_iso_date(personal.fecha_nacimiento),
                personal.direccion,
                int(personal.activo),
                personal.puesto,
                personal.turno,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, personal: Personal) -> None:
        if not personal.id:
            raise ValidationError("No se puede actualizar personal sin id.")
        personal.validar()
        self._con.execute(
            """
            UPDATE personal SET
                tipo_documento = ?,
                documento = ?,
                nombre = ?,
                apellidos = ?,
                telefono = ?,
                email = ?,
                fecha_nacimiento = ?,
                direccion = ?,
                activo = ?,
                puesto = ?,
                turno = ?
            WHERE id = ?
            """,
            (
                personal.tipo_documento.value,
                personal.documento,
                personal.nombre,
                personal.apellidos,
                personal.telefono,
                personal.email,
                format_iso_date(personal.fecha_nacimiento),
                personal.direccion,
                int(personal.activo),
                personal.puesto,
                personal.turno,
                personal.id,
            ),
        )
        self._con.commit()

    def delete(self, personal_id: int) -> None:
        self._con.execute("UPDATE personal SET activo = 0 WHERE id = ?", (personal_id,))
        self._con.commit()

    def get_by_id(self, personal_id: int) -> Optional[Personal]:
        return self._consultas.get_by_id(personal_id)

    def get_id_by_documento(
        self,
        tipo_documento: TipoDocumento | str,
        documento: str,
    ) -> Optional[int]:
        return self._consultas.get_id_by_documento(tipo_documento, documento)

    def get_id_by_nombre(self, nombre: str, apellidos: Optional[str] = None) -> Optional[int]:
        return self._consultas.get_id_by_nombre(nombre, apellidos)

    def list_all(self, *, solo_activos: bool = True) -> List[Personal]:
        return self._consultas.list_all(solo_activos=solo_activos)

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Personal]:
        return self._consultas.search(
            texto=texto,
            puesto=puesto,
            tipo_documento=tipo_documento,
            documento=documento,
            activo=activo,
        )

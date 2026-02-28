# infrastructure/sqlite/repos_medicos.py
"""
Repositorio SQLite para Médicos.

Responsabilidades:
- CRUD de médicos
- Búsquedas con filtros (especialidad, activo, texto libre)
- Conversión fila <-> modelo de dominio

No contiene:
- Lógica de agenda
- Validaciones de calendario
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Medico
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.common.search_utils import like_value, normalize_search_text
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date
from clinicdesk.app.infrastructure.sqlite.pii_crypto import get_connection_pii_cipher


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MedicosRepository:
    """
    Repositorio de acceso a datos para médicos.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection
        self._pii_cipher = get_connection_pii_cipher(connection)

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, medico: Medico) -> int:
        medico.validar()

        cur = self._con.execute(
            """
            INSERT INTO medicos (
                tipo_documento, documento,
                nombre, apellidos,
                telefono, email,
                fecha_nacimiento, direccion,
                activo,
                num_colegiado, especialidad
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                medico.tipo_documento.value,
                medico.documento,
                medico.nombre,
                medico.apellidos,
                _encrypt_pii(self._pii_cipher, medico.telefono),
                _encrypt_pii(self._pii_cipher, medico.email),
                format_iso_date(medico.fecha_nacimiento),
                _encrypt_pii(self._pii_cipher, medico.direccion),
                int(medico.activo),
                medico.num_colegiado,
                medico.especialidad,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, medico: Medico) -> None:
        if not medico.id:
            raise ValidationError("No se puede actualizar un médico sin id.")

        medico.validar()

        self._con.execute(
            """
            UPDATE medicos SET
                tipo_documento = ?,
                documento = ?,
                nombre = ?,
                apellidos = ?,
                telefono = ?,
                email = ?,
                fecha_nacimiento = ?,
                direccion = ?,
                activo = ?,
                num_colegiado = ?,
                especialidad = ?
            WHERE id = ?
            """,
            (
                medico.tipo_documento.value,
                medico.documento,
                medico.nombre,
                medico.apellidos,
                _encrypt_pii(self._pii_cipher, medico.telefono),
                _encrypt_pii(self._pii_cipher, medico.email),
                format_iso_date(medico.fecha_nacimiento),
                _encrypt_pii(self._pii_cipher, medico.direccion),
                int(medico.activo),
                medico.num_colegiado,
                medico.especialidad,
                medico.id,
            ),
        )
        self._con.commit()

    def delete(self, medico_id: int) -> None:
        self._con.execute(
            "UPDATE medicos SET activo = 0 WHERE id = ?",
            (medico_id,),
        )
        self._con.commit()

    def get_by_id(self, medico_id: int) -> Optional[Medico]:
        row = self._con.execute(
            "SELECT * FROM medicos WHERE id = ?",
            (medico_id,),
        ).fetchone()

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
            "SELECT id FROM medicos WHERE tipo_documento = ? AND documento = ?",
            (tipo, documento),
        ).fetchone()
        return int(row["id"]) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Medico]:
        sql = "SELECT * FROM medicos"
        params: list = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY apellidos, nombre"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicosRepository.list_all: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        especialidad: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Medico]:
        texto = normalize_search_text(texto)
        especialidad = normalize_search_text(especialidad)
        documento = normalize_search_text(documento)
        tipo_documento_value = normalize_search_text(
            tipo_documento.value if tipo_documento else None
        )

        clauses: list[str] = []
        params: list = []

        if texto:
            clauses.append(
                "(nombre LIKE ? COLLATE NOCASE OR apellidos LIKE ? COLLATE NOCASE "
                "OR documento LIKE ? COLLATE NOCASE OR num_colegiado LIKE ? COLLATE NOCASE)"
            )
            like = like_value(texto)
            params.extend([like, like, like, like])

        if especialidad:
            clauses.append("especialidad LIKE ? COLLATE NOCASE")
            params.append(like_value(especialidad))

        if tipo_documento_value:
            clauses.append("tipo_documento LIKE ? COLLATE NOCASE")
            params.append(like_value(tipo_documento_value))

        if documento:
            clauses.append("documento LIKE ? COLLATE NOCASE")
            params.append(like_value(documento))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM medicos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY apellidos, nombre"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicosRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Medico:
        return Medico(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=row["documento"],
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=_decrypt_pii(self._pii_cipher, row["telefono"]),
            email=_decrypt_pii(self._pii_cipher, row["email"]),
            fecha_nacimiento=parse_iso_date(row["fecha_nacimiento"]),
            direccion=_decrypt_pii(self._pii_cipher, row["direccion"]),
            activo=bool(row["activo"]),
            num_colegiado=row["num_colegiado"],
            especialidad=row["especialidad"],
        )


def _encrypt_pii(cipher, value: str | None) -> str | None:
    if cipher is None:
        return value
    return cipher.encrypt_optional(value)


def _decrypt_pii(cipher, value: str | None) -> str | None:
    if cipher is None:
        return value
    return cipher.decrypt_optional(value)

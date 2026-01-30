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

import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.date_utils import format_iso_date, parse_iso_date


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class PersonalRepository:
    """
    Repositorio de acceso a datos para personal.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, personal: Personal) -> int:
        """
        Inserta un nuevo registro de personal y devuelve su id.
        """
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
        """
        Actualiza un registro de personal existente.
        """
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
        """
        Borrado lógico: marca el personal como inactivo.
        """
        self._con.execute(
            "UPDATE personal SET activo = 0 WHERE id = ?",
            (personal_id,),
        )
        self._con.commit()

    def get_by_id(self, personal_id: int) -> Optional[Personal]:
        """
        Obtiene un registro de personal por id.
        """
        row = self._con.execute(
            "SELECT * FROM personal WHERE id = ?",
            (personal_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    def get_id_by_documento(
        self,
        tipo_documento: TipoDocumento | str,
        documento: str,
    ) -> Optional[int]:
        """
        Obtiene el id del personal a partir del tipo + documento.
        """
        if not documento:
            return None
        tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else str(tipo_documento)
        row = self._con.execute(
            "SELECT id FROM personal WHERE tipo_documento = ? AND documento = ?",
            (tipo, documento),
        ).fetchone()
        return int(row["id"]) if row else None

    def get_id_by_nombre(self, nombre: str, apellidos: Optional[str] = None) -> Optional[int]:
        """
        Obtiene el id del personal por nombre y apellidos (búsqueda flexible).
        """
        if not nombre:
            return None
        clauses = ["nombre LIKE ?"]
        params: list = [f\"%{nombre}%\"]
        if apellidos:
            clauses.append("apellidos LIKE ?")
            params.append(f\"%{apellidos}%\")
        sql = "SELECT id FROM personal WHERE " + " AND ".join(clauses) + " ORDER BY apellidos, nombre"
        row = self._con.execute(sql, params).fetchone()
        return int(row["id"]) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Personal]:
        """
        Lista todo el personal.
        """
        sql = "SELECT * FROM personal"
        params: list = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY apellidos, nombre"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        puesto: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Personal]:
        """
        Búsqueda flexible de personal.

        Parámetros:
        - texto: busca en nombre, apellidos y documento
        - puesto: filtro exacto por puesto
        - tipo_documento: filtro por tipo
        - documento: documento exacto
        - activo: True / False / None (None = todos)
        """
        clauses: list[str] = []
        params: list = []

        if texto:
            clauses.append("(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ?)")
            like = f"%{texto}%"
            params.extend([like, like, like])

        if puesto:
            clauses.append("puesto = ?")
            params.append(puesto)

        if tipo_documento:
            clauses.append("tipo_documento = ?")
            params.append(tipo_documento.value)

        if documento:
            clauses.append("documento = ?")
            params.append(documento)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM personal"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY apellidos, nombre"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Personal:
        """
        Convierte una fila SQLite en un modelo Personal.
        """
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

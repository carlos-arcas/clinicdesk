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

import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Medico
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MedicosRepository:
    """
    Repositorio de acceso a datos para médicos.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, medico: Medico) -> int:
        """
        Inserta un nuevo médico y devuelve su id.
        """
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
                medico.telefono,
                medico.email,
                medico.fecha_nacimiento.isoformat() if medico.fecha_nacimiento else None,
                medico.direccion,
                int(medico.activo),
                medico.num_colegiado,
                medico.especialidad,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, medico: Medico) -> None:
        """
        Actualiza un médico existente.
        """
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
                medico.telefono,
                medico.email,
                medico.fecha_nacimiento.isoformat() if medico.fecha_nacimiento else None,
                medico.direccion,
                int(medico.activo),
                medico.num_colegiado,
                medico.especialidad,
                medico.id,
            ),
        )
        self._con.commit()

    def delete(self, medico_id: int) -> None:
        """
        Borrado lógico: marca el médico como inactivo.
        """
        self._con.execute(
            "UPDATE medicos SET activo = 0 WHERE id = ?",
            (medico_id,),
        )
        self._con.commit()

    def get_by_id(self, medico_id: int) -> Optional[Medico]:
        """
        Obtiene un médico por id.
        """
        row = self._con.execute(
            "SELECT * FROM medicos WHERE id = ?",
            (medico_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Medico]:
        """
        Lista todos los médicos.
        """
        sql = "SELECT * FROM medicos"
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
        especialidad: Optional[str] = None,
        tipo_documento: Optional[TipoDocumento] = None,
        documento: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Medico]:
        """
        Búsqueda flexible de médicos.

        Parámetros:
        - texto: busca en nombre, apellidos, documento y num_colegiado
        - especialidad: filtro exacto por especialidad
        - tipo_documento: filtro por tipo
        - documento: documento exacto
        - activo: True / False / None (None = todos)
        """
        clauses: list[str] = []
        params: list = []

        if texto:
            clauses.append(
                "(nombre LIKE ? OR apellidos LIKE ? OR documento LIKE ? OR num_colegiado LIKE ?)"
            )
            like = f"%{texto}%"
            params.extend([like, like, like, like])

        if especialidad:
            clauses.append("especialidad = ?")
            params.append(especialidad)

        if tipo_documento:
            clauses.append("tipo_documento = ?")
            params.append(tipo_documento.value)

        if documento:
            clauses.append("documento = ?")
            params.append(documento)

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM medicos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY apellidos, nombre"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Medico:
        """
        Convierte una fila SQLite en un modelo Medico.
        """
        return Medico(
            id=row["id"],
            tipo_documento=TipoDocumento(row["tipo_documento"]),
            documento=row["documento"],
            nombre=row["nombre"],
            apellidos=row["apellidos"],
            telefono=row["telefono"],
            email=row["email"],
            fecha_nacimiento=None if row["fecha_nacimiento"] is None else row["fecha_nacimiento"],
            direccion=row["direccion"],
            activo=bool(row["activo"]),
            num_colegiado=row["num_colegiado"],
            especialidad=row["especialidad"],
        )

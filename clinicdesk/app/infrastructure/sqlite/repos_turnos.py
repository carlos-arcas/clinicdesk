# infrastructure/sqlite/repos_turnos.py
"""
Repositorio SQLite para Turnos.

Responsabilidades:
- CRUD de turnos laborales
- Listado y filtrado de turnos activos
- Conversión fila <-> modelo de dominio (ligero)

Notas:
- Los turnos son entidades relativamente estáticas
  (mañana, tarde, guardia, etc.).
- Se usan como referencia en calendarios de médicos y personal.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from clinicdesk.app.common.search_utils import has_search_values, like_value, normalize_search_text
from clinicdesk.app.domain.exceptions import ValidationError


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Modelo simple de Turno (ligero, sin herencia compleja)
# ---------------------------------------------------------------------


class Turno:
    """
    Modelo simple de Turno laboral.

    Se define aquí para no contaminar el dominio con
    detalles puramente organizativos.
    """

    def __init__(
        self,
        *,
        id: Optional[int] = None,
        nombre: str,
        hora_inicio: str,
        hora_fin: str,
        activo: bool = True,
    ) -> None:
        self.id = id
        self.nombre = nombre
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.activo = activo

    def validar(self) -> None:
        if not self.nombre.strip():
            raise ValidationError("El nombre del turno es obligatorio.")
        if not self.hora_inicio or not self.hora_fin:
            raise ValidationError("hora_inicio y hora_fin son obligatorias.")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class TurnosRepository:
    """
    Repositorio de acceso a datos para turnos.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, turno: Turno) -> int:
        """
        Inserta un nuevo turno y devuelve su id.
        """
        turno.validar()

        cur = self._con.execute(
            """
            INSERT INTO turnos (
                nombre, hora_inicio, hora_fin, activo
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                turno.nombre,
                turno.hora_inicio,
                turno.hora_fin,
                int(turno.activo),
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, turno: Turno) -> None:
        """
        Actualiza un turno existente.
        """
        if not turno.id:
            raise ValidationError("No se puede actualizar un turno sin id.")

        turno.validar()

        self._con.execute(
            """
            UPDATE turnos SET
                nombre = ?,
                hora_inicio = ?,
                hora_fin = ?,
                activo = ?
            WHERE id = ?
            """,
            (
                turno.nombre,
                turno.hora_inicio,
                turno.hora_fin,
                int(turno.activo),
                turno.id,
            ),
        )
        self._con.commit()

    def delete(self, turno_id: int) -> None:
        """
        Borrado lógico: marca el turno como inactivo.
        """
        self._con.execute(
            "UPDATE turnos SET activo = 0 WHERE id = ?",
            (turno_id,),
        )
        self._con.commit()

    def get_by_id(self, turno_id: int) -> Optional[Turno]:
        """
        Obtiene un turno por id.
        """
        row = self._con.execute(
            "SELECT * FROM turnos WHERE id = ?",
            (turno_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Turno]:
        """
        Lista todos los turnos.
        """
        sql = "SELECT * FROM turnos"
        params = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY hora_inicio"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en TurnosRepository.list_all: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        nombre: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Turno]:
        """
        Búsqueda de turnos.

        Parámetros:
        - nombre: búsqueda parcial por nombre
        - activo: True / False / None
        """
        nombre = normalize_search_text(nombre)

        if not has_search_values(nombre):
            logger.info("TurnosRepository.search skipped (filtros vacíos).")
            return []

        clauses = []
        params = []

        if nombre:
            clauses.append("nombre LIKE ? COLLATE NOCASE")
            params.append(like_value(nombre))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM turnos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY hora_inicio"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en TurnosRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Turno:
        """
        Convierte una fila SQLite en un modelo Turno.
        """
        return Turno(
            id=row["id"],
            nombre=row["nombre"],
            hora_inicio=row["hora_inicio"],
            hora_fin=row["hora_fin"],
            activo=bool(row["activo"]),
        )

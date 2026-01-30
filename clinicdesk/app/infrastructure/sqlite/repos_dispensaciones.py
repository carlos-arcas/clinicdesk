# infrastructure/sqlite/repos_dispensaciones.py
"""
Repositorio SQLite para Dispensaciones de medicamentos.

Responsabilidades:
- Registrar dispensaciones vinculadas a recetas
- Registrar quién dispensa (personal)
- Registrar fecha y hora exacta
- Registrar incidencias conscientes (override con notas)

No contiene:
- Lógica de validación de calendario
- Lógica de stock
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from clinicdesk.app.domain.exceptions import ValidationError


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Modelo ligero de dispensación
# ---------------------------------------------------------------------


@dataclass(slots=True)
class Dispensacion:
    """
    Registro de dispensación de un medicamento.
    """

    id: Optional[int] = None

    receta_id: int = 0
    receta_linea_id: int = 0
    medicamento_id: int = 0

    personal_id: int = 0

    cantidad: int = 0
    fecha_hora: str = ""  # ISO datetime

    incidencia: bool = False
    notas_incidencia: Optional[str] = None

    def validar(self) -> None:
        if self.receta_id <= 0:
            raise ValidationError("receta_id inválido.")
        if self.receta_linea_id <= 0:
            raise ValidationError("receta_linea_id inválido.")
        if self.medicamento_id <= 0:
            raise ValidationError("medicamento_id inválido.")
        if self.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if self.cantidad <= 0:
            raise ValidationError("cantidad debe ser mayor que 0.")
        if not self.fecha_hora:
            raise ValidationError("fecha_hora obligatoria.")
        if self.incidencia and not self.notas_incidencia:
            raise ValidationError(
                "Una dispensación con incidencia requiere notas explicativas."
            )


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class DispensacionesRepository:
    """
    Repositorio de acceso a datos para dispensaciones.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, dispensacion: Dispensacion) -> int:
        """
        Inserta una dispensación y devuelve su id.
        """
        dispensacion.validar()

        cur = self._con.execute(
            """
            INSERT INTO dispensaciones (
                receta_id,
                receta_linea_id,
                medicamento_id,
                personal_id,
                cantidad,
                fecha_hora,
                incidencia,
                notas_incidencia
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dispensacion.receta_id,
                dispensacion.receta_linea_id,
                dispensacion.medicamento_id,
                dispensacion.personal_id,
                dispensacion.cantidad,
                dispensacion.fecha_hora,
                int(dispensacion.incidencia),
                dispensacion.notas_incidencia,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def get_by_id(self, dispensacion_id: int) -> Optional[Dispensacion]:
        """
        Obtiene una dispensación por id.
        """
        row = self._con.execute(
            "SELECT * FROM dispensaciones WHERE id = ?",
            (dispensacion_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    def delete(self, dispensacion_id: int) -> None:
        """
        Borrado lógico: marca la dispensación como inactiva.
        """
        self._con.execute("UPDATE dispensaciones SET activo = 0 WHERE id = ?", (dispensacion_id,))
        self._con.commit()

    # --------------------------------------------------------------
    # Consultas de auditoría
    # --------------------------------------------------------------

    def list_by_receta(self, receta_id: int) -> List[Dispensacion]:
        """
        Lista todas las dispensaciones de una receta.
        """
        try:
            rows = self._con.execute(
                """
                SELECT * FROM dispensaciones
                WHERE receta_id = ? AND activo = 1
                ORDER BY fecha_hora
                """,
                (receta_id,),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en DispensacionesRepository.list_by_receta: %s", exc)
            return []

        return [self._row_to_model(r) for r in rows]

    def list_by_personal(
        self,
        personal_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Dispensacion]:
        """
        Lista dispensaciones realizadas por un miembro del personal.
        """
        if personal_id <= 0:
            raise ValidationError("personal_id inválido.")

        clauses = ["personal_id = ?"]
        params = [personal_id]

        if desde:
            clauses.append("fecha_hora >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha_hora <= ?")
            params.append(hasta)

        clauses.append("activo = 1")
        sql = "SELECT * FROM dispensaciones WHERE " + " AND ".join(clauses) + " ORDER BY fecha_hora DESC"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en DispensacionesRepository.list_by_personal: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def list_con_incidencias(
        self,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Dispensacion]:
        """
        Lista dispensaciones que contienen incidencias.
        """
        clauses = ["incidencia = 1"]
        params = []

        if desde:
            clauses.append("fecha_hora >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha_hora <= ?")
            params.append(hasta)

        clauses.append("activo = 1")
        sql = "SELECT * FROM dispensaciones WHERE " + " AND ".join(clauses) + " ORDER BY fecha_hora DESC"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en DispensacionesRepository.list_con_incidencias: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Dispensacion:
        """
        Convierte fila SQLite en Dispensacion.
        """
        return Dispensacion(
            id=row["id"],
            receta_id=row["receta_id"],
            receta_linea_id=row["receta_linea_id"],
            medicamento_id=row["medicamento_id"],
            personal_id=row["personal_id"],
            cantidad=row["cantidad"],
            fecha_hora=row["fecha_hora"],
            incidencia=bool(row["incidencia"]),
            notas_incidencia=row["notas_incidencia"],
        )

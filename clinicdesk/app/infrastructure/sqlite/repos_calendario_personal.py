# infrastructure/sqlite/repos_calendario_personal.py
"""
Repositorio SQLite para el calendario laboral del personal.

Responsabilidades:
- CRUD de bloques de trabajo diarios (calendario_personal)
- Consultas por personal, fecha y rango
- Utilidades para detectar días sin cuadrante cargado

No contiene:
- Lógica de dispensación
- Validación de incidencias
- Código de UI
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Modelo ligero de bloque de calendario
# ---------------------------------------------------------------------


@dataclass(slots=True)
class BloqueCalendarioPersonal:
    """
    Bloque de trabajo diario de un miembro del personal.
    """

    id: Optional[int] = None
    personal_id: int = 0
    fecha: str = ""                 # YYYY-MM-DD
    turno_id: int = 0

    hora_inicio_override: Optional[str] = None  # HH:MM
    hora_fin_override: Optional[str] = None     # HH:MM
    observaciones: Optional[str] = None
    activo: bool = True

    def validar(self) -> None:
        if self.personal_id <= 0:
            raise ValidationError("personal_id inválido.")
        if not self.fecha:
            raise ValidationError("fecha obligatoria.")
        if self.turno_id <= 0:
            raise ValidationError("turno_id inválido.")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class CalendarioPersonalRepository:
    """
    Repositorio de acceso a datos para calendario_personal.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, bloque: BloqueCalendarioPersonal) -> int:
        """
        Inserta un bloque de calendario y devuelve su id.
        """
        bloque.validar()

        cur = self._con.execute(
            """
            INSERT INTO calendario_personal (
                personal_id, fecha, turno_id,
                hora_inicio_override, hora_fin_override,
                observaciones, activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bloque.personal_id,
                bloque.fecha,
                bloque.turno_id,
                bloque.hora_inicio_override,
                bloque.hora_fin_override,
                bloque.observaciones,
                int(bloque.activo),
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, bloque: BloqueCalendarioPersonal) -> None:
        """
        Actualiza un bloque de calendario existente.
        """
        if not bloque.id:
            raise ValidationError("No se puede actualizar un bloque sin id.")

        bloque.validar()

        self._con.execute(
            """
            UPDATE calendario_personal SET
                personal_id = ?,
                fecha = ?,
                turno_id = ?,
                hora_inicio_override = ?,
                hora_fin_override = ?,
                observaciones = ?,
                activo = ?
            WHERE id = ?
            """,
            (
                bloque.personal_id,
                bloque.fecha,
                bloque.turno_id,
                bloque.hora_inicio_override,
                bloque.hora_fin_override,
                bloque.observaciones,
                int(bloque.activo),
                bloque.id,
            ),
        )
        self._con.commit()

    def delete(self, bloque_id: int) -> None:
        """
        Borrado lógico: marca el bloque como inactivo.
        """
        self._con.execute(
            "UPDATE calendario_personal SET activo = 0 WHERE id = ?",
            (bloque_id,),
        )
        self._con.commit()

    def get_by_id(self, bloque_id: int) -> Optional[BloqueCalendarioPersonal]:
        """
        Obtiene un bloque por id.
        """
        row = self._con.execute(
            "SELECT * FROM calendario_personal WHERE id = ?",
            (bloque_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Consultas útiles
    # --------------------------------------------------------------

    def list_by_personal(
        self,
        personal_id: int,
        *,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        solo_activos: bool = True,
    ) -> List[BloqueCalendarioPersonal]:
        """
        Lista bloques de calendario de un miembro del personal,
        opcionalmente por rango de fechas.
        """
        if personal_id <= 0:
            raise ValidationError("personal_id inválido.")

        clauses = ["personal_id = ?"]
        params = [personal_id]

        if fecha_desde:
            clauses.append("fecha >= ?")
            params.append(fecha_desde)

        if fecha_hasta:
            clauses.append("fecha <= ?")
            params.append(fecha_hasta)

        if solo_activos:
            clauses.append("activo = 1")

        sql = "SELECT * FROM calendario_personal WHERE " + " AND ".join(clauses)
        sql += " ORDER BY fecha"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def exists_for_personal_fecha(
        self,
        personal_id: int,
        fecha: str,
        *,
        solo_activos: bool = True,
    ) -> bool:
        """
        Indica si existe algún bloque de calendario para un miembro del personal
        en una fecha concreta.
        Útil para detectar 'día sin cuadrante cargado'.
        """
        clauses = ["personal_id = ?", "fecha = ?"]
        params = [personal_id, fecha]

        if solo_activos:
            clauses.append("activo = 1")

        sql = (
            "SELECT 1 FROM calendario_personal WHERE "
            + " AND ".join(clauses)
            + " LIMIT 1"
        )

        row = self._con.execute(sql, params).fetchone()
        return row is not None

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> BloqueCalendarioPersonal:
        """
        Convierte una fila SQLite en un BloqueCalendarioPersonal.
        """
        return BloqueCalendarioPersonal(
            id=row["id"],
            personal_id=row["personal_id"],
            fecha=row["fecha"],
            turno_id=row["turno_id"],
            hora_inicio_override=row["hora_inicio_override"],
            hora_fin_override=row["hora_fin_override"],
            observaciones=row["observaciones"],
            activo=bool(row["activo"]),
        )

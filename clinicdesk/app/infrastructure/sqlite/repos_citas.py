# infrastructure/sqlite/repos_citas.py
"""
Repositorio SQLite para Citas.

Responsabilidades:
- CRUD de citas
- Consultas por paciente, médico, sala y rango temporal
- Conversión fila <-> modelo de dominio

No contiene:
- Validación de disponibilidad de médicos
- Validación de cuadrantes
- Gestión de incidencias
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

from clinicdesk.app.domain.enums import EstadoCita
from clinicdesk.app.domain.modelos import Cita
from clinicdesk.app.domain.exceptions import ValidationError


logger = logging.getLogger(__name__)


def _parse_dt(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class CitasRepository:
    """
    Repositorio de acceso a datos para citas.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, cita: Cita) -> int:
        """
        Inserta una cita y devuelve su id.
        """
        cita.validar()

        cur = self._con.execute(
            """
            INSERT INTO citas (
                paciente_id,
                medico_id,
                sala_id,
                inicio,
                fin,
                motivo,
                notas,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cita.paciente_id,
                cita.medico_id,
                cita.sala_id,
                cita.inicio,
                cita.fin,
                cita.motivo,
                cita.notas,
                cita.estado.value,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, cita: Cita) -> None:
        """
        Actualiza una cita existente.
        """
        if not cita.id:
            raise ValidationError("No se puede actualizar una cita sin id.")

        cita.validar()

        self._con.execute(
            """
            UPDATE citas SET
                paciente_id = ?,
                medico_id = ?,
                sala_id = ?,
                inicio = ?,
                fin = ?,
                motivo = ?,
                notas = ?,
                estado = ?
            WHERE id = ?
            """,
            (
                cita.paciente_id,
                cita.medico_id,
                cita.sala_id,
                cita.inicio,
                cita.fin,
                cita.motivo,
                cita.notas,
                cita.estado.value,
                cita.id,
            ),
        )
        self._con.commit()

    def delete(self, cita_id: int) -> None:
        """
        Borrado lógico: marca la cita como inactiva.
        """
        self._con.execute("UPDATE citas SET activo = 0 WHERE id = ?", (cita_id,))
        self._con.commit()

    def get_by_id(self, cita_id: int) -> Optional[Cita]:
        """
        Obtiene una cita por id.
        """
        row = self._con.execute(
            "SELECT * FROM citas WHERE id = ?",
            (cita_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Consultas
    # --------------------------------------------------------------

    def list_by_paciente(
        self,
        paciente_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Cita]:
        """
        Lista citas de un paciente.
        """
        if paciente_id <= 0:
            raise ValidationError("paciente_id inválido.")

        return self._list_by_field("paciente_id", paciente_id, desde=desde, hasta=hasta, method_name="list_by_paciente")

    def list_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Cita]:
        """
        Lista citas de un médico.
        """
        if medico_id <= 0:
            raise ValidationError("medico_id inválido.")

        return self._list_by_field("medico_id", medico_id, desde=desde, hasta=hasta, method_name="list_by_medico")

    def list_by_sala(
        self,
        sala_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Cita]:
        """
        Lista citas de una sala.
        """
        if sala_id <= 0:
            raise ValidationError("sala_id inválido.")

        return self._list_by_field("sala_id", sala_id, desde=desde, hasta=hasta, method_name="list_by_sala")

    def list_by_estado(
        self,
        estado: str,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Cita]:
        """
        Lista citas por estado (PROGRAMADA, CANCELADA, REALIZADA…).
        """
        if not estado:
            raise ValidationError("estado obligatorio.")

        return self._list_by_field("estado", estado, desde=desde, hasta=hasta, method_name="list_by_estado")

    def list_in_range(self, *, desde: datetime, hasta: datetime) -> List[Cita]:
        """Lista citas activas cuyo inicio cae dentro del rango temporal."""
        if hasta < desde:
            raise ValidationError("Rango inválido: 'hasta' debe ser >= 'desde'.")

        try:
            rows = self._con.execute(
                """
                SELECT *
                FROM citas
                WHERE activo = 1
                  AND inicio >= ?
                  AND inicio <= ?
                ORDER BY inicio
                """,
                (desde, hasta),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en CitasRepository.list_in_range: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Cita:
        """
        Convierte fila SQLite en Cita.
        """
        return Cita(
            id=row["id"],
            paciente_id=row["paciente_id"],
            medico_id=row["medico_id"],
            sala_id=row["sala_id"],
            inicio=_parse_dt(row["inicio"]),
            fin=_parse_dt(row["fin"]),
            motivo=row["motivo"],
            notas=row["notas"],
            estado=EstadoCita(row["estado"]),
        )

    def _list_by_field(
        self,
        field_name: str,
        field_value: int | str,
        *,
        desde: Optional[str],
        hasta: Optional[str],
        method_name: str,
    ) -> List[Cita]:
        clauses = [f"{field_name} = ?", "activo = 1"]
        params: list[int | str] = [field_value]
        if desde:
            clauses.append("inicio >= ?")
            params.append(desde)
        if hasta:
            clauses.append("inicio <= ?")
            params.append(hasta)
        sql = "SELECT * FROM citas WHERE " + " AND ".join(clauses) + " ORDER BY inicio"
        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en CitasRepository.%s: %s", method_name, exc)
            return []
        return [self._row_to_model(r) for r in rows]

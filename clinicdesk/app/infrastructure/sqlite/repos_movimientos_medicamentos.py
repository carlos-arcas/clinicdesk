# infrastructure/sqlite/repos_movimientos_medicamentos.py
"""
Repositorio SQLite para movimientos de medicamentos.

Responsabilidades:
- Registrar entradas, salidas y ajustes de stock
- Mantener histórico completo para auditoría
- Consultas por medicamento, tipo y rango temporal

No contiene:
- Actualización directa del stock actual
- Lógica de dispensación
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
# Modelo ligero de movimiento
# ---------------------------------------------------------------------


@dataclass(slots=True)
class MovimientoMedicamento:
    """
    Movimiento de stock de un medicamento.
    """

    id: Optional[int] = None

    medicamento_id: int = 0
    tipo: str = ""              # ENTRADA / SALIDA / AJUSTE
    cantidad: int = 0

    fecha_hora: str = ""        # ISO datetime
    personal_id: Optional[int] = None

    motivo: Optional[str] = None
    referencia: Optional[str] = None  # receta, albarán, inventario, etc.

    def validar(self) -> None:
        if self.medicamento_id <= 0:
            raise ValidationError("medicamento_id inválido.")
        if not self.tipo.strip():
            raise ValidationError("tipo de movimiento obligatorio.")
        if self.cantidad == 0:
            raise ValidationError("cantidad no puede ser 0.")
        if not self.fecha_hora:
            raise ValidationError("fecha_hora obligatoria.")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MovimientosMedicamentosRepository:
    """
    Repositorio de acceso a datos para movimientos_medicamentos.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, movimiento: MovimientoMedicamento) -> int:
        """
        Inserta un movimiento y devuelve su id.
        """
        movimiento.validar()

        cur = self._con.execute(
            """
            INSERT INTO movimientos_medicamentos (
                medicamento_id,
                tipo,
                cantidad,
                fecha_hora,
                personal_id,
                motivo,
                referencia
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movimiento.medicamento_id,
                movimiento.tipo,
                movimiento.cantidad,
                movimiento.fecha_hora,
                movimiento.personal_id,
                movimiento.motivo,
                movimiento.referencia,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def get_by_id(self, movimiento_id: int) -> Optional[MovimientoMedicamento]:
        """
        Obtiene un movimiento por id.
        """
        row = self._con.execute(
            "SELECT * FROM movimientos_medicamentos WHERE id = ?",
            (movimiento_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    def delete(self, movimiento_id: int) -> None:
        """
        Borrado lógico: marca el movimiento como inactivo.
        """
        self._con.execute("UPDATE movimientos_medicamentos SET activo = 0 WHERE id = ?", (movimiento_id,))
        self._con.commit()

    # --------------------------------------------------------------
    # Consultas de auditoría
    # --------------------------------------------------------------

    def list_by_medicamento(
        self,
        medicamento_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[MovimientoMedicamento]:
        """
        Lista movimientos de un medicamento.
        """
        if medicamento_id <= 0:
            raise ValidationError("medicamento_id inválido.")

        clauses = ["medicamento_id = ?"]
        params = [medicamento_id]

        if desde:
            clauses.append("fecha_hora >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha_hora <= ?")
            params.append(hasta)

        clauses.append("activo = 1")
        sql = "SELECT * FROM movimientos_medicamentos WHERE " + " AND ".join(clauses) + " ORDER BY fecha_hora DESC"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MovimientosMedicamentosRepository.list_by_medicamento: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def list_by_tipo(
        self,
        tipo: str,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[MovimientoMedicamento]:
        """
        Lista movimientos por tipo (ENTRADA / SALIDA / AJUSTE).
        """
        if not tipo.strip():
            raise ValidationError("tipo obligatorio.")

        clauses = ["tipo = ?"]
        params = [tipo]

        if desde:
            clauses.append("fecha_hora >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha_hora <= ?")
            params.append(hasta)

        clauses.append("activo = 1")
        sql = "SELECT * FROM movimientos_medicamentos WHERE " + " AND ".join(clauses) + " ORDER BY fecha_hora DESC"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MovimientosMedicamentosRepository.list_by_tipo: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> MovimientoMedicamento:
        """
        Convierte fila SQLite en MovimientoMedicamento.
        """
        return MovimientoMedicamento(
            id=row["id"],
            medicamento_id=row["medicamento_id"],
            tipo=row["tipo"],
            cantidad=row["cantidad"],
            fecha_hora=row["fecha_hora"],
            personal_id=row["personal_id"],
            motivo=row["motivo"],
            referencia=row["referencia"],
        )

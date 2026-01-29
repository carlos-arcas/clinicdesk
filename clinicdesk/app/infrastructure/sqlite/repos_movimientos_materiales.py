# infrastructure/sqlite/repos_movimientos_materiales.py
"""
Repositorio SQLite para movimientos de materiales.

Responsabilidades:
- Registrar entradas, salidas y ajustes de stock de material
- Mantener histórico completo para auditoría
- Consultas por material, tipo y rango temporal

No contiene:
- Actualización directa del stock actual
- Lógica de uso/consumo
- Código de UI
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Modelo ligero de movimiento
# ---------------------------------------------------------------------


@dataclass(slots=True)
class MovimientoMaterial:
    """
    Movimiento de stock de un material.
    """

    id: Optional[int] = None

    material_id: int = 0
    tipo: str = ""              # ENTRADA / SALIDA / AJUSTE
    cantidad: int = 0

    fecha_hora: str = ""        # ISO datetime
    personal_id: Optional[int] = None

    motivo: Optional[str] = None
    referencia: Optional[str] = None  # servicio, inventario, incidencia, etc.

    def validar(self) -> None:
        if self.material_id <= 0:
            raise ValidationError("material_id inválido.")
        if not self.tipo.strip():
            raise ValidationError("tipo de movimiento obligatorio.")
        if self.cantidad == 0:
            raise ValidationError("cantidad no puede ser 0.")
        if not self.fecha_hora:
            raise ValidationError("fecha_hora obligatoria.")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MovimientosMaterialesRepository:
    """
    Repositorio de acceso a datos para movimientos_materiales.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, movimiento: MovimientoMaterial) -> int:
        """
        Inserta un movimiento y devuelve su id.
        """
        movimiento.validar()

        cur = self._con.execute(
            """
            INSERT INTO movimientos_materiales (
                material_id,
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
                movimiento.material_id,
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

    def get_by_id(self, movimiento_id: int) -> Optional[MovimientoMaterial]:
        """
        Obtiene un movimiento por id.
        """
        row = self._con.execute(
            "SELECT * FROM movimientos_materiales WHERE id = ?",
            (movimiento_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    def delete(self, movimiento_id: int) -> None:
        """
        Borrado físico (registro de auditoría).
        """
        self._con.execute(
            "DELETE FROM movimientos_materiales WHERE id = ?",
            (movimiento_id,),
        )
        self._con.commit()

    # --------------------------------------------------------------
    # Consultas de auditoría
    # --------------------------------------------------------------

    def list_by_material(
        self,
        material_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[MovimientoMaterial]:
        """
        Lista movimientos de un material.
        """
        if material_id <= 0:
            raise ValidationError("material_id inválido.")

        clauses = ["material_id = ?"]
        params = [material_id]

        if desde:
            clauses.append("fecha_hora >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha_hora <= ?")
            params.append(hasta)

        sql = (
            "SELECT * FROM movimientos_materiales WHERE "
            + " AND ".join(clauses)
            + " ORDER BY fecha_hora DESC"
        )

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def list_by_tipo(
        self,
        tipo: str,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[MovimientoMaterial]:
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

        sql = (
            "SELECT * FROM movimientos_materiales WHERE "
            + " AND ".join(clauses)
            + " ORDER BY fecha_hora DESC"
        )

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> MovimientoMaterial:
        """
        Convierte fila SQLite en MovimientoMaterial.
        """
        return MovimientoMaterial(
            id=row["id"],
            material_id=row["material_id"],
            tipo=row["tipo"],
            cantidad=row["cantidad"],
            fecha_hora=row["fecha_hora"],
            personal_id=row["personal_id"],
            motivo=row["motivo"],
            referencia=row["referencia"],
        )

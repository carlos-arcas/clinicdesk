# infrastructure/sqlite/repos_medicamentos.py
"""
Repositorio SQLite para Medicamentos.

Responsabilidades:
- CRUD del catálogo de medicamentos
- Consulta y filtrado
- Gestión directa del stock actual (cantidad_en_almacen)

No contiene:
- Movimientos de stock (eso va en repos_movimientos_medicamentos)
- Lógica de dispensación
- Código de UI
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Medicamento
from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MedicamentosRepository:
    """
    Repositorio de acceso a datos para medicamentos.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, medicamento: Medicamento) -> int:
        """
        Inserta un nuevo medicamento y devuelve su id.
        """
        medicamento.validar()

        cur = self._con.execute(
            """
            INSERT INTO medicamentos (
                nombre_compuesto,
                nombre_comercial,
                cantidad_en_almacen,
                activo
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                medicamento.nombre_compuesto,
                medicamento.nombre_comercial,
                medicamento.cantidad_en_almacen,
                int(medicamento.activo),
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, medicamento: Medicamento) -> None:
        """
        Actualiza un medicamento existente.
        """
        if not medicamento.id:
            raise ValidationError("No se puede actualizar un medicamento sin id.")

        medicamento.validar()

        self._con.execute(
            """
            UPDATE medicamentos SET
                nombre_compuesto = ?,
                nombre_comercial = ?,
                cantidad_en_almacen = ?,
                activo = ?
            WHERE id = ?
            """,
            (
                medicamento.nombre_compuesto,
                medicamento.nombre_comercial,
                medicamento.cantidad_en_almacen,
                int(medicamento.activo),
                medicamento.id,
            ),
        )
        self._con.commit()

    def delete(self, medicamento_id: int) -> None:
        """
        Borrado lógico: marca el medicamento como inactivo.
        """
        self._con.execute(
            "UPDATE medicamentos SET activo = 0 WHERE id = ?",
            (medicamento_id,),
        )
        self._con.commit()

    def get_by_id(self, medicamento_id: int) -> Optional[Medicamento]:
        """
        Obtiene un medicamento por id.
        """
        row = self._con.execute(
            "SELECT * FROM medicamentos WHERE id = ?",
            (medicamento_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    def get_id_by_nombre(self, nombre: str) -> Optional[int]:
        """
        Obtiene el id del medicamento por nombre comercial o compuesto.
        """
        if not nombre:
            return None
        row = self._con.execute(
            """
            SELECT id FROM medicamentos
            WHERE nombre_comercial = ? OR nombre_compuesto = ?
            ORDER BY nombre_comercial
            """,
            (nombre, nombre),
        ).fetchone()
        return int(row["id"]) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Medicamento]:
        """
        Lista todos los medicamentos.
        """
        sql = "SELECT * FROM medicamentos"
        params = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY nombre_comercial"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Medicamento]:
        """
        Búsqueda flexible de medicamentos.

        Parámetros:
        - texto: busca en nombre comercial y compuesto
        - activo: True / False / None (None = todos)
        """
        clauses = []
        params = []

        if texto:
            clauses.append(
                "(nombre_comercial LIKE ? OR nombre_compuesto LIKE ?)"
            )
            like = f"%{texto}%"
            params.extend([like, like])

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM medicamentos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY nombre_comercial"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Stock
    # --------------------------------------------------------------

    def update_stock(self, medicamento_id: int, nueva_cantidad: int) -> None:
        """
        Actualiza directamente la cantidad en almacén.

        Nota:
        - El uso normal debería ser a través de movimientos,
          pero este método existe para correcciones manuales.
        """
        if nueva_cantidad < 0:
            raise ValidationError("La cantidad no puede ser negativa.")

        self._con.execute(
            """
            UPDATE medicamentos
            SET cantidad_en_almacen = ?
            WHERE id = ?
            """,
            (nueva_cantidad, medicamento_id),
        )
        self._con.commit()

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Medicamento:
        """
        Convierte fila SQLite en modelo Medicamento.
        """
        return Medicamento(
            id=row["id"],
            nombre_compuesto=row["nombre_compuesto"],
            nombre_comercial=row["nombre_comercial"],
            cantidad_en_almacen=row["cantidad_en_almacen"],
            activo=bool(row["activo"]),
        )

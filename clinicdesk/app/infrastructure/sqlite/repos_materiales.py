# infrastructure/sqlite/repos_materiales.py
"""
Repositorio SQLite para Materiales.

Responsabilidades:
- CRUD del catálogo de materiales
- Diferenciación fungible / no fungible
- Gestión directa del stock actual

No contiene:
- Movimientos de stock (eso va en repos_movimientos_materiales)
- Lógica de uso/consumo
- Código de UI
"""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Material
from clinicdesk.app.common.search_utils import has_search_values, like_value, normalize_search_text
from clinicdesk.app.domain.exceptions import ValidationError


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class MaterialesRepository:
    """
    Repositorio de acceso a datos para materiales.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, material: Material) -> int:
        """
        Inserta un nuevo material y devuelve su id.
        """
        material.validar()

        cur = self._con.execute(
            """
            INSERT INTO materiales (
                nombre,
                fungible,
                cantidad_en_almacen,
                activo
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                material.nombre,
                int(material.fungible),
                material.cantidad_en_almacen,
                int(material.activo),
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, material: Material) -> None:
        """
        Actualiza un material existente.
        """
        if not material.id:
            raise ValidationError("No se puede actualizar un material sin id.")

        material.validar()

        self._con.execute(
            """
            UPDATE materiales SET
                nombre = ?,
                fungible = ?,
                cantidad_en_almacen = ?,
                activo = ?
            WHERE id = ?
            """,
            (
                material.nombre,
                int(material.fungible),
                material.cantidad_en_almacen,
                int(material.activo),
                material.id,
            ),
        )
        self._con.commit()

    def delete(self, material_id: int) -> None:
        """
        Borrado lógico: marca el material como inactivo.
        """
        self._con.execute(
            "UPDATE materiales SET activo = 0 WHERE id = ?",
            (material_id,),
        )
        self._con.commit()

    def get_by_id(self, material_id: int) -> Optional[Material]:
        """
        Obtiene un material por id.
        """
        row = self._con.execute(
            "SELECT * FROM materiales WHERE id = ?",
            (material_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activos: bool = True) -> List[Material]:
        """
        Lista todos los materiales.
        """
        sql = "SELECT * FROM materiales"
        params = []

        if solo_activos:
            sql += " WHERE activo = 1"

        sql += " ORDER BY nombre"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MaterialesRepository.list_all: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        texto: Optional[str] = None,
        fungible: Optional[bool] = None,
        activo: Optional[bool] = True,
    ) -> List[Material]:
        """
        Búsqueda flexible de materiales.

        Parámetros:
        - texto: busca en nombre
        - fungible: True / False / None (None = todos)
        - activo: True / False / None (None = todos)
        """
        texto = normalize_search_text(texto)

        if not has_search_values(texto):
            logger.info("MaterialesRepository.search skipped (filtros vacíos).")
            return []

        clauses = []
        params = []

        if texto:
            clauses.append("nombre LIKE ? COLLATE NOCASE")
            params.append(like_value(texto))

        if fungible is not None:
            clauses.append("fungible = ?")
            params.append(int(fungible))

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT * FROM materiales"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY nombre"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MaterialesRepository.search: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Stock
    # --------------------------------------------------------------

    def update_stock(self, material_id: int, nueva_cantidad: int) -> None:
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
            UPDATE materiales
            SET cantidad_en_almacen = ?
            WHERE id = ?
            """,
            (nueva_cantidad, material_id),
        )
        self._con.commit()

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Material:
        """
        Convierte fila SQLite en modelo Material.
        """
        return Material(
            id=row["id"],
            nombre=row["nombre"],
            fungible=bool(row["fungible"]),
            cantidad_en_almacen=row["cantidad_en_almacen"],
            activo=bool(row["activo"]),
        )

# infrastructure/sqlite/repos_salas.py
"""
Repositorio SQLite para Salas.

Responsabilidades:
- CRUD de salas
- Búsqueda y filtrado por tipo y estado
- Conversión fila <-> modelo de dominio

No contiene:
- Lógica de citas
- Lógica de disponibilidad
- Código de UI
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Sala
from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class SalasRepository:
    """
    Repositorio de acceso a datos para salas.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, sala: Sala) -> int:
        """
        Inserta una nueva sala y devuelve su id.
        """
        sala.validar()

        cur = self._con.execute(
            """
            INSERT INTO salas (
                nombre, tipo, ubicacion, activa
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                sala.nombre,
                sala.tipo.value,
                sala.ubicacion,
                int(sala.activa),
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, sala: Sala) -> None:
        """
        Actualiza una sala existente.
        """
        if not sala.id:
            raise ValidationError("No se puede actualizar una sala sin id.")

        sala.validar()

        self._con.execute(
            """
            UPDATE salas SET
                nombre = ?,
                tipo = ?,
                ubicacion = ?,
                activa = ?
            WHERE id = ?
            """,
            (
                sala.nombre,
                sala.tipo.value,
                sala.ubicacion,
                int(sala.activa),
                sala.id,
            ),
        )
        self._con.commit()

    def delete(self, sala_id: int) -> None:
        """
        Borrado lógico: marca la sala como inactiva.
        """
        self._con.execute(
            "UPDATE salas SET activa = 0 WHERE id = ?",
            (sala_id,),
        )
        self._con.commit()

    def get_by_id(self, sala_id: int) -> Optional[Sala]:
        """
        Obtiene una sala por id.
        """
        row = self._con.execute(
            "SELECT * FROM salas WHERE id = ?",
            (sala_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Listado y búsqueda
    # --------------------------------------------------------------

    def list_all(self, *, solo_activas: bool = True) -> List[Sala]:
        """
        Lista todas las salas.
        """
        sql = "SELECT * FROM salas"
        params = []

        if solo_activas:
            sql += " WHERE activa = 1"

        sql += " ORDER BY nombre"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def search(
        self,
        *,
        tipo: Optional[TipoSala] = None,
        activa: Optional[bool] = True,
        texto: Optional[str] = None,
    ) -> List[Sala]:
        """
        Búsqueda flexible de salas.

        Parámetros:
        - tipo: filtra por tipo de sala
        - activa: True / False / None (None = todas)
        - texto: busca en nombre y ubicación
        """
        clauses = []
        params = []

        if tipo:
            clauses.append("tipo = ?")
            params.append(tipo.value)

        if activa is not None:
            clauses.append("activa = ?")
            params.append(int(activa))

        if texto:
            clauses.append("(nombre LIKE ? OR ubicacion LIKE ?)")
            like = f"%{texto}%"
            params.extend([like, like])

        sql = "SELECT * FROM salas"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY nombre"

        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_model(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> Sala:
        """
        Convierte una fila SQLite en un modelo Sala.
        """
        return Sala(
            id=row["id"],
            nombre=row["nombre"],
            tipo=TipoSala(row["tipo"]),
            ubicacion=row["ubicacion"],
            activa=bool(row["activa"]),
        )

# infrastructure/sqlite/repos_recetas.py
"""
Repositorio SQLite para Recetas y Líneas de Receta.

Responsabilidades:
- CRUD de recetas (cabecera) y líneas
- Consultas por paciente, médico y rangos
- Conversión fila <-> modelo de dominio

No contiene:
- Lógica de dispensación
- Validación de stock
- Código de UI
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from clinicdesk.app.domain.modelos import Receta, RecetaLinea
from clinicdesk.app.domain.exceptions import ValidationError


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class RecetasRepository:
    """
    Repositorio de acceso a datos para recetas y receta_lineas.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # Recetas (cabecera)
    # --------------------------------------------------------------

    def create_receta(self, receta: Receta) -> int:
        """
        Inserta una receta (cabecera) y devuelve su id.
        """
        receta.validar()

        cur = self._con.execute(
            """
            INSERT INTO recetas (
                paciente_id, medico_id, fecha, observaciones
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                receta.paciente_id,
                receta.medico_id,
                receta.fecha.isoformat(sep=" ", timespec="seconds"),
                receta.observaciones,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update_receta(self, receta: Receta) -> None:
        """
        Actualiza una receta (cabecera).
        """
        if not receta.id:
            raise ValidationError("No se puede actualizar receta sin id.")

        receta.validar()

        self._con.execute(
            """
            UPDATE recetas SET
                paciente_id = ?,
                medico_id = ?,
                fecha = ?,
                observaciones = ?
            WHERE id = ?
            """,
            (
                receta.paciente_id,
                receta.medico_id,
                receta.fecha.isoformat(sep=" ", timespec="seconds"),
                receta.observaciones,
                receta.id,
            ),
        )
        self._con.commit()

    def get_receta_by_id(self, receta_id: int) -> Optional[Receta]:
        """
        Obtiene una receta por id.
        """
        row = self._con.execute(
            "SELECT * FROM recetas WHERE id = ?",
            (receta_id,),
        ).fetchone()

        return self._row_to_receta(row) if row else None

    def delete_receta(self, receta_id: int) -> None:
        """
        Borrado físico de la receta.
        Por schema, las líneas se borran en cascada.
        """
        self._con.execute("DELETE FROM recetas WHERE id = ?", (receta_id,))
        self._con.commit()

    # --------------------------------------------------------------
    # Líneas de receta
    # --------------------------------------------------------------

    def add_linea(self, linea: RecetaLinea) -> int:
        """
        Inserta una línea de receta y devuelve su id.
        """
        linea.validar()

        cur = self._con.execute(
            """
            INSERT INTO receta_lineas (
                receta_id, medicamento_id, dosis, duracion_dias, instrucciones
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                linea.receta_id,
                linea.medicamento_id,
                linea.dosis,
                linea.duracion_dias,
                linea.instrucciones,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update_linea(self, linea: RecetaLinea) -> None:
        """
        Actualiza una línea de receta.
        """
        if not linea.id:
            raise ValidationError("No se puede actualizar línea sin id.")

        linea.validar()

        self._con.execute(
            """
            UPDATE receta_lineas SET
                receta_id = ?,
                medicamento_id = ?,
                dosis = ?,
                duracion_dias = ?,
                instrucciones = ?
            WHERE id = ?
            """,
            (
                linea.receta_id,
                linea.medicamento_id,
                linea.dosis,
                linea.duracion_dias,
                linea.instrucciones,
                linea.id,
            ),
        )
        self._con.commit()

    def delete_linea(self, linea_id: int) -> None:
        """
        Borrado físico de una línea.
        """
        self._con.execute("DELETE FROM receta_lineas WHERE id = ?", (linea_id,))
        self._con.commit()

    def list_lineas_by_receta(self, receta_id: int) -> List[RecetaLinea]:
        """
        Lista todas las líneas de una receta.
        """
        rows = self._con.execute(
            """
            SELECT * FROM receta_lineas
            WHERE receta_id = ?
            ORDER BY id
            """,
            (receta_id,),
        ).fetchall()

        return [self._row_to_linea(r) for r in rows]

    # --------------------------------------------------------------
    # Consultas típicas
    # --------------------------------------------------------------

    def list_recetas_by_paciente(
        self,
        paciente_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        """
        Lista recetas de un paciente, opcionalmente por rango.
        """
        if paciente_id <= 0:
            raise ValidationError("paciente_id inválido.")

        clauses = ["paciente_id = ?"]
        params = [paciente_id]

        if desde:
            clauses.append("fecha >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha <= ?")
            params.append(hasta)

        sql = "SELECT * FROM recetas WHERE " + " AND ".join(clauses) + " ORDER BY fecha DESC"
        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_receta(r) for r in rows]

    def list_recetas_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[Receta]:
        """
        Lista recetas emitidas por un médico, opcionalmente por rango.
        """
        if medico_id <= 0:
            raise ValidationError("medico_id inválido.")

        clauses = ["medico_id = ?"]
        params = [medico_id]

        if desde:
            clauses.append("fecha >= ?")
            params.append(desde)

        if hasta:
            clauses.append("fecha <= ?")
            params.append(hasta)

        sql = "SELECT * FROM recetas WHERE " + " AND ".join(clauses) + " ORDER BY fecha DESC"
        rows = self._con.execute(sql, params).fetchall()
        return [self._row_to_receta(r) for r in rows]

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_receta(self, row: sqlite3.Row) -> Receta:
        """
        Convierte fila SQLite en Receta.
        """
        # La fecha se guarda como TEXT ISO; el modelo espera datetime.
        # Se delega el parseo a datetime.fromisoformat si el formato incluye hora.
        from datetime import datetime

        return Receta(
            id=row["id"],
            paciente_id=row["paciente_id"],
            medico_id=row["medico_id"],
            fecha=datetime.fromisoformat(row["fecha"]),
            observaciones=row["observaciones"],
        )

    def _row_to_linea(self, row: sqlite3.Row) -> RecetaLinea:
        """
        Convierte fila SQLite en RecetaLinea.
        """
        return RecetaLinea(
            id=row["id"],
            receta_id=row["receta_id"],
            medicamento_id=row["medicamento_id"],
            dosis=row["dosis"],
            duracion_dias=row["duracion_dias"],
            instrucciones=row["instrucciones"],
        )

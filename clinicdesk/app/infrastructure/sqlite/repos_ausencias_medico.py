# infrastructure/sqlite/repos_ausencias_medico.py
"""
Repositorio SQLite para ausencias de médicos.

Responsabilidades:
- CRUD de ausencias (ausencias_medico)
- Consultas por médico y rango temporal
- Utilidad para detectar solapes (ausencia activa que cubre un rango)

No contiene:
- Lógica de citas
- Políticas de warnings/overrides
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
# Modelo ligero de ausencia
# ---------------------------------------------------------------------


@dataclass(slots=True)
class AusenciaMedico:
    """
    Ausencia de un médico.

    Campos inicio/fin:
    - Se guardan como TEXT en ISO:
      "YYYY-MM-DD" o "YYYY-MM-DD HH:MM:SS"
    - La comparación lexicográfica funciona correctamente con ISO.
    """

    id: Optional[int] = None
    medico_id: int = 0

    inicio: str = ""  # ISO date o datetime
    fin: str = ""     # ISO date o datetime

    tipo: str = ""    # VACACIONES/BAJA/PERMISO/...
    motivo: Optional[str] = None

    aprobado_por_personal_id: Optional[int] = None
    creado_en: str = ""  # ISO datetime

    def validar(self) -> None:
        if self.medico_id <= 0:
            raise ValidationError("medico_id inválido.")
        if not self.inicio or not self.fin:
            raise ValidationError("inicio y fin son obligatorios.")
        if self.fin < self.inicio:
            raise ValidationError("fin no puede ser anterior a inicio.")
        if not self.tipo.strip():
            raise ValidationError("tipo de ausencia obligatorio.")
        if not self.creado_en:
            raise ValidationError("creado_en obligatorio (ISO datetime).")


# ---------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------


class AusenciasMedicoRepository:
    """
    Repositorio de acceso a datos para ausencias_medico.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._con = connection

    # --------------------------------------------------------------
    # CRUD
    # --------------------------------------------------------------

    def create(self, ausencia: AusenciaMedico) -> int:
        """
        Inserta una ausencia y devuelve su id.
        """
        ausencia.validar()

        cur = self._con.execute(
            """
            INSERT INTO ausencias_medico (
                medico_id, inicio, fin, tipo, motivo,
                aprobado_por_personal_id, creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ausencia.medico_id,
                ausencia.inicio,
                ausencia.fin,
                ausencia.tipo,
                ausencia.motivo,
                ausencia.aprobado_por_personal_id,
                ausencia.creado_en,
            ),
        )
        self._con.commit()
        return int(cur.lastrowid)

    def update(self, ausencia: AusenciaMedico) -> None:
        """
        Actualiza una ausencia existente.
        """
        if not ausencia.id:
            raise ValidationError("No se puede actualizar una ausencia sin id.")

        ausencia.validar()

        self._con.execute(
            """
            UPDATE ausencias_medico SET
                medico_id = ?,
                inicio = ?,
                fin = ?,
                tipo = ?,
                motivo = ?,
                aprobado_por_personal_id = ?,
                creado_en = ?
            WHERE id = ?
            """,
            (
                ausencia.medico_id,
                ausencia.inicio,
                ausencia.fin,
                ausencia.tipo,
                ausencia.motivo,
                ausencia.aprobado_por_personal_id,
                ausencia.creado_en,
                ausencia.id,
            ),
        )
        self._con.commit()

    def delete(self, ausencia_id: int) -> None:
        """
        Borrado lógico: marca la ausencia como inactiva.
        """
        self._con.execute("UPDATE ausencias_medico SET activo = 0 WHERE id = ?", (ausencia_id,))
        self._con.commit()

    def get_by_id(self, ausencia_id: int) -> Optional[AusenciaMedico]:
        """
        Obtiene una ausencia por id.
        """
        row = self._con.execute(
            "SELECT * FROM ausencias_medico WHERE id = ?",
            (ausencia_id,),
        ).fetchone()

        return self._row_to_model(row) if row else None

    # --------------------------------------------------------------
    # Consultas útiles
    # --------------------------------------------------------------

    def list_by_medico(
        self,
        medico_id: int,
        *,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
    ) -> List[AusenciaMedico]:
        """
        Lista ausencias de un médico, opcionalmente filtradas por rango.

        Nota:
        - El filtro se aplica sobre (fin >= desde) y (inicio <= hasta)
          para capturar solapes.
        """
        if medico_id <= 0:
            raise ValidationError("medico_id inválido.")

        clauses = ["medico_id = ?"]
        params = [medico_id]

        if desde:
            clauses.append("fin >= ?")
            params.append(desde)

        if hasta:
            clauses.append("inicio <= ?")
            params.append(hasta)

        clauses.append("activo = 1")
        sql = "SELECT * FROM ausencias_medico WHERE " + " AND ".join(clauses)
        sql += " ORDER BY inicio"

        try:
            rows = self._con.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en AusenciasMedicoRepository.list_by_medico: %s", exc)
            return []
        return [self._row_to_model(r) for r in rows]

    def exists_overlap(
        self,
        medico_id: int,
        inicio: str,
        fin: str,
    ) -> bool:
        """
        Indica si existe una ausencia que solape con el rango [inicio, fin].
        """
        if medico_id <= 0:
            raise ValidationError("medico_id inválido.")
        if not inicio or not fin:
            raise ValidationError("inicio y fin son obligatorios.")
        if fin < inicio:
            raise ValidationError("fin no puede ser anterior a inicio.")

        row = self._con.execute(
            """
            SELECT 1
            FROM ausencias_medico
            WHERE medico_id = ?
              AND inicio <= ?
              AND fin >= ?
              AND activo = 1
            LIMIT 1
            """,
            (medico_id, fin, inicio),
        ).fetchone()

        return row is not None

    # --------------------------------------------------------------
    # Interno
    # --------------------------------------------------------------

    def _row_to_model(self, row: sqlite3.Row) -> AusenciaMedico:
        """
        Convierte fila SQLite en AusenciaMedico.
        """
        return AusenciaMedico(
            id=row["id"],
            medico_id=row["medico_id"],
            inicio=row["inicio"],
            fin=row["fin"],
            tipo=row["tipo"],
            motivo=row["motivo"],
            aprobado_por_personal_id=row["aprobado_por_personal_id"],
            creado_en=row["creado_en"],
        )

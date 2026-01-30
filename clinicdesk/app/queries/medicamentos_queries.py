from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3

from clinicdesk.app.common.search_utils import has_search_values, like_value, normalize_search_text


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MedicamentoRow:
    id: int
    nombre_comercial: str
    nombre_compuesto: str
    stock: int
    activo: bool


@dataclass(frozen=True, slots=True)
class MovimientoMedicamentoRow:
    id: int
    fecha_hora: str
    tipo: str
    cantidad: int
    personal: str
    motivo: str
    referencia: str


class MedicamentosQueries:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    def search(
        self,
        *,
        texto: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 500,
    ) -> List[MedicamentoRow]:
        texto = normalize_search_text(texto)

        if not has_search_values(texto):
            logger.info("Medicamentos search skipped (filtros vacíos).")
            return []

        clauses = []
        params: List[object] = []

        if texto:
            like = like_value(texto)
            clauses.append(
                "(nombre_comercial LIKE ? COLLATE NOCASE OR nombre_compuesto LIKE ? COLLATE NOCASE)"
            )
            params.extend([like, like])

        if activo is not None:
            clauses.append("activo = ?")
            params.append(int(activo))

        sql = "SELECT id, nombre_comercial, nombre_compuesto, cantidad_en_almacen, activo FROM medicamentos"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY nombre_comercial LIMIT ?"
        params.append(int(limit))

        try:
            rows = self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicamentosQueries.search: %s", exc)
            return []
        return [
            MedicamentoRow(
                id=row["id"],
                nombre_comercial=row["nombre_comercial"],
                nombre_compuesto=row["nombre_compuesto"],
                stock=int(row["cantidad_en_almacen"]),
                activo=bool(row["activo"]),
            )
            for row in rows
        ]

    def list_movimientos(self, medicamento_id: int, *, limit: int = 200) -> List[MovimientoMedicamentoRow]:
        try:
            rows = self._conn.execute(
                """
                SELECT mm.id, mm.fecha_hora, mm.tipo, mm.cantidad,
                       (p.nombre || ' ' || p.apellidos) AS personal,
                       mm.motivo, mm.referencia
                FROM movimientos_medicamentos mm
                LEFT JOIN personal p ON p.id = mm.personal_id
                WHERE mm.medicamento_id = ? AND mm.activo = 1
                ORDER BY mm.fecha_hora DESC
                LIMIT ?
                """,
                (medicamento_id, int(limit)),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error("Error SQL en MedicamentosQueries.list_movimientos: %s", exc)
            return []

        return [
            MovimientoMedicamentoRow(
                id=row["id"],
                fecha_hora=row["fecha_hora"],
                tipo=row["tipo"],
                cantidad=int(row["cantidad"]),
                personal=row["personal"] or "",
                motivo=row["motivo"] or "",
                referencia=row["referencia"] or "",
            )
            for row in rows
        ]

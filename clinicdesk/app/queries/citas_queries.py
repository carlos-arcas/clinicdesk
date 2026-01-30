from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import logging

from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.container import AppContainer


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CitaRow:
    id: int
    inicio: str
    fin: str
    paciente_id: int
    paciente_nombre: str
    medico_id: int
    medico_nombre: str
    sala_id: int
    sala_nombre: str
    estado: str
    motivo: Optional[str]


class CitasQueries:
    """Consultas de lectura para Citas (UI/auditoría)."""

    def __init__(self, container: AppContainer) -> None:
        self._c = container

    def list_by_date(self, yyyy_mm_dd: str) -> List[CitaRow]:
        yyyy_mm_dd = normalize_search_text(yyyy_mm_dd)
        if not yyyy_mm_dd:
            logger.info("Citas list_by_date skipped (fecha vacía).")
            return []

        try:
            rows = self._c.connection.execute(
                """
                SELECT
                    c.id,
                    c.inicio,
                    c.fin,
                    c.paciente_id,
                    (p.nombre || ' ' || p.apellidos) AS paciente_nombre,
                    c.medico_id,
                    (m.nombre || ' ' || m.apellidos) AS medico_nombre,
                    c.sala_id,
                    s.nombre AS sala_nombre,
                    c.estado,
                    c.motivo
                FROM citas c
                JOIN pacientes p ON p.id = c.paciente_id
                JOIN medicos m ON m.id = c.medico_id
                JOIN salas s ON s.id = c.sala_id
                WHERE c.inicio LIKE ? AND c.activo = 1
                ORDER BY c.inicio
                """,
                (f"{yyyy_mm_dd}%",),
            ).fetchall()
        except Exception as exc:
            logger.error("Error SQL en CitasQueries.list_by_date: %s", exc)
            return []

        out: List[CitaRow] = []
        for r in rows:
            out.append(
                CitaRow(
                    id=int(r["id"]),
                    inicio=r["inicio"],
                    fin=r["fin"],
                    paciente_id=int(r["paciente_id"]),
                    paciente_nombre=r["paciente_nombre"],
                    medico_id=int(r["medico_id"]),
                    medico_nombre=r["medico_nombre"],
                    sala_id=int(r["sala_id"]),
                    sala_nombre=r["sala_nombre"],
                    estado=r["estado"],
                    motivo=r["motivo"],
                )
            )
        return out

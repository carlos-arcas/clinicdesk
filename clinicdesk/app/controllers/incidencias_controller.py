from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import QWidget

from clinicdesk.app.container import AppContainer
from clinicdesk.app.queries.incidencias_queries import IncidenciaRow, IncidenciasQueries
from clinicdesk.app.ui.error_presenter import present_error


class IncidenciasController:
    """Controlador de auditoría de incidencias (solo lectura)."""

    def __init__(self, parent: QWidget, container: AppContainer) -> None:
        self._parent = parent
        self._c = container
        self._q = IncidenciasQueries(container)

    def search(
        self,
        *,
        tipo: Optional[str],
        estado: Optional[str],
        severidad: Optional[str],
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        limit: int = 500,
    ) -> List[IncidenciaRow]:
        try:
            return self._q.list(
                tipo=tipo or None,
                estado=estado or None,
                severidad=severidad or None,
                fecha_desde=fecha_desde or None,
                fecha_hasta=fecha_hasta or None,
                limit=limit,
            )
        except Exception as e:
            present_error(self._parent, e)
            return []

    def get_detail(self, incidencia_id: int) -> Optional[IncidenciaRow]:
        try:
            return self._q.get_by_id(incidencia_id)
        except Exception as e:
            present_error(self._parent, e)
            return None

from __future__ import annotations

import sqlite3

from PySide6.QtCore import QObject, Signal

from clinicdesk.app.application.confirmaciones import (
    FiltrosConfirmacionesDTO,
    ObtenerConfirmacionesCitas,
    PaginacionConfirmacionesDTO,
)
from clinicdesk.app.common.search_utils import has_search_values
from clinicdesk.app.queries.confirmaciones_queries import ConfirmacionesQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries


class CargaPacientesWorker(QObject):
    finished_ok = Signal(object)
    finished_error = Signal(str)
    finished = Signal()

    def __init__(self, db_path: str, activo: bool, texto: str) -> None:
        super().__init__()
        self._db_path = db_path
        self._activo = activo
        self._texto = texto

    def run(self) -> None:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self._db_path)
            connection.row_factory = sqlite3.Row
            queries = PacientesQueries(connection)
            base_rows = queries.list_all(activo=self._activo)
            rows = (
                base_rows
                if not has_search_values(self._texto)
                else queries.search(texto=self._texto, activo=self._activo)
            )
            self.finished_ok.emit({"rows": rows, "total_base": len(base_rows)})
        except Exception as exc:  # noqa: BLE001
            self.finished_error.emit(exc.__class__.__name__)
        finally:
            if connection is not None:
                connection.close()
            self.finished.emit()


class CargaConfirmacionesWorker(QObject):
    finished_ok = Signal(object)
    finished_error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        *,
        db_path: str,
        filtros: FiltrosConfirmacionesDTO,
        paginacion: PaginacionConfirmacionesDTO,
        riesgo_uc: object,
        salud_uc: object,
    ) -> None:
        super().__init__()
        self._db_path = db_path
        self._filtros = filtros
        self._paginacion = paginacion
        self._riesgo_uc = riesgo_uc
        self._salud_uc = salud_uc

    def run(self) -> None:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self._db_path)
            connection.row_factory = sqlite3.Row
            use_case = ObtenerConfirmacionesCitas(
                queries=ConfirmacionesQueries(connection),
                obtener_riesgo_uc=self._riesgo_uc,
                obtener_salud_uc=self._salud_uc,
            )
            result = use_case.ejecutar(self._filtros, self._paginacion)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.finished_error.emit(exc.__class__.__name__)
        finally:
            if connection is not None:
                connection.close()
            self.finished.emit()

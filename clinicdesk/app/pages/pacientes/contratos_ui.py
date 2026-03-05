from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QPushButton, QTableWidget, QWidget

from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


@dataclass(slots=True)
class PacientesUIRefs:
    filtros: FiltroListadoWidget
    btn_nuevo: QPushButton
    btn_editar: QPushButton
    btn_desactivar: QPushButton
    btn_historial: QPushButton
    btn_csv: QPushButton
    table: QTableWidget
    estado_pantalla: EstadoPantallaWidget
    contenido_tabla: QWidget

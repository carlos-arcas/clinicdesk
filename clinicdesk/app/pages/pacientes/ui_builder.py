from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QVBoxLayout, QWidget

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pacientes.contratos_ui import PacientesUIRefs
from clinicdesk.app.pages.shared.filtro_listado import FiltroListadoWidget
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


def _configurar_accesibilidad(i18n: I18nManager, ui: PacientesUIRefs) -> None:
    ui.table.setAccessibleName(i18n.t("quick_search.title.pacientes"))
    ui.btn_nuevo.setAccessibleName(i18n.t("pacientes.acciones.nuevo"))
    ui.btn_editar.setAccessibleName(i18n.t("pacientes.acciones.editar"))
    ui.btn_desactivar.setAccessibleName(i18n.t("pacientes.acciones.desactivar"))
    ui.btn_historial.setAccessibleName(i18n.t("pacientes.historial.boton"))
    ui.btn_csv.setAccessibleName(i18n.t("menu.csv"))
    ui.btn_historial.setToolTip(i18n.t("pacientes.historial.boton"))
    QWidget.setTabOrder(ui.filtros.txt_buscar, ui.filtros.cbo_estado)
    QWidget.setTabOrder(ui.filtros.cbo_estado, ui.btn_nuevo)
    QWidget.setTabOrder(ui.btn_nuevo, ui.btn_editar)
    QWidget.setTabOrder(ui.btn_editar, ui.btn_desactivar)
    QWidget.setTabOrder(ui.btn_desactivar, ui.btn_historial)
    QWidget.setTabOrder(ui.btn_historial, ui.btn_csv)
    QWidget.setTabOrder(ui.btn_csv, ui.table)


def build_pacientes_ui(parent: QWidget, i18n: I18nManager, *, can_write: bool, headers: list[str]) -> PacientesUIRefs:
    root = QVBoxLayout(parent)

    filtros = FiltroListadoWidget(parent)
    acciones = _build_acciones(i18n=i18n, can_write=can_write)
    tabla = _build_tabla(headers=headers)
    estado_pantalla, contenido_tabla = _build_estado_pantalla(parent=parent, i18n=i18n, tabla=tabla)

    root.addWidget(filtros)
    root.addLayout(acciones[0])
    root.addWidget(estado_pantalla)
    refs = PacientesUIRefs(
        filtros=filtros,
        btn_nuevo=acciones[1],
        btn_editar=acciones[2],
        btn_desactivar=acciones[3],
        btn_historial=acciones[4],
        btn_csv=acciones[5],
        table=tabla,
        estado_pantalla=estado_pantalla,
        contenido_tabla=contenido_tabla,
    )
    _configurar_accesibilidad(i18n, refs)
    return refs


def _build_acciones(
    i18n: I18nManager, *, can_write: bool
) -> tuple[QHBoxLayout, QPushButton, QPushButton, QPushButton, QPushButton, QPushButton]:
    actions = QHBoxLayout()
    btn_nuevo = QPushButton(i18n.t("pacientes.acciones.nuevo"))
    btn_editar = QPushButton(i18n.t("pacientes.acciones.editar"))
    btn_desactivar = QPushButton(i18n.t("pacientes.acciones.desactivar"))
    btn_historial = QPushButton(i18n.t("pacientes.historial.boton"))
    btn_csv = QPushButton(i18n.t("menu.csv"))

    btn_editar.setEnabled(False)
    btn_desactivar.setEnabled(False)
    btn_historial.setEnabled(False)
    btn_nuevo.setEnabled(can_write)

    actions.addWidget(btn_nuevo)
    actions.addWidget(btn_editar)
    actions.addWidget(btn_desactivar)
    actions.addWidget(btn_historial)
    actions.addWidget(btn_csv)
    actions.addStretch(1)
    return actions, btn_nuevo, btn_editar, btn_desactivar, btn_historial, btn_csv


def _build_tabla(*, headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setColumnHidden(0, True)
    table.horizontalHeader().setStretchLastSection(True)
    table.setContextMenuPolicy(Qt.CustomContextMenu)
    return table


def _build_estado_pantalla(
    *, parent: QWidget, i18n: I18nManager, tabla: QTableWidget
) -> tuple[EstadoPantallaWidget, QWidget]:
    estado_pantalla = EstadoPantallaWidget(i18n, parent)
    contenido = QWidget(parent)
    contenido_layout = QVBoxLayout(contenido)
    contenido_layout.setContentsMargins(0, 0, 0, 0)
    contenido_layout.addWidget(tabla)
    estado_pantalla.set_content(contenido)
    return estado_pantalla, contenido

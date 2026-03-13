from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.contratos_ui import ConfirmacionesUIRefs
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


def build_confirmaciones_ui(parent: QWidget, i18n: I18nManager) -> ConfirmacionesUIRefs:
    root = QVBoxLayout(parent)
    lbl_title = QLabel()
    banner = QLabel()
    btn_ir_prediccion = QPushButton()
    root.addWidget(lbl_title)

    banner_row = QHBoxLayout()
    banner_row.addWidget(banner, 1)
    banner_row.addWidget(btn_ir_prediccion)
    root.addLayout(banner_row)

    cmb_rango = QComboBox()
    desde = QDateEdit()
    hasta = QDateEdit()
    cmb_riesgo = QComboBox()
    cmb_recordatorio = QComboBox()
    txt_buscar = QLineEdit()
    txt_buscar.setPlaceholderText(i18n.t("quick_search.placeholder.confirmaciones"))
    btn_actualizar = QPushButton()
    filtros = QHBoxLayout()
    for widget in (cmb_rango, desde, hasta, cmb_riesgo, cmb_recordatorio, txt_buscar, btn_actualizar):
        filtros.addWidget(widget)
    root.addLayout(filtros)

    chk_todo_visible = QCheckBox()
    lbl_seleccionadas = QLabel()
    seleccion_row = QHBoxLayout()
    seleccion_row.addWidget(chk_todo_visible)
    seleccion_row.addWidget(lbl_seleccionadas)
    seleccion_row.addStretch(1)
    root.addLayout(seleccion_row)

    table = QTableWidget(0, 9)
    table.setEditTriggers(QTableWidget.NoEditTriggers)

    lbl_totales = QLabel()
    btn_prev = QPushButton()
    btn_next = QPushButton()
    footer = QHBoxLayout()
    footer.addWidget(lbl_totales)
    footer.addStretch(1)
    footer.addWidget(btn_prev)
    footer.addWidget(btn_next)

    contenido_tabla = QWidget(parent)
    contenido_layout = QVBoxLayout(contenido_tabla)
    contenido_layout.setContentsMargins(0, 0, 0, 0)
    contenido_layout.addWidget(table)
    contenido_layout.addLayout(footer)

    estado_pantalla = EstadoPantallaWidget(i18n, parent)
    estado_pantalla.set_content(contenido_tabla)
    root.addWidget(estado_pantalla)

    lbl_title.setAccessibleName("confirmaciones_titulo")
    txt_buscar.setAccessibleName("confirmaciones_busqueda")
    btn_actualizar.setAccessibleName("confirmaciones_actualizar")
    QWidget.setTabOrder(btn_ir_prediccion, cmb_rango)
    QWidget.setTabOrder(cmb_rango, desde)
    QWidget.setTabOrder(desde, hasta)
    QWidget.setTabOrder(hasta, cmb_riesgo)
    QWidget.setTabOrder(cmb_riesgo, cmb_recordatorio)
    QWidget.setTabOrder(cmb_recordatorio, txt_buscar)
    QWidget.setTabOrder(txt_buscar, btn_actualizar)
    QWidget.setTabOrder(btn_actualizar, chk_todo_visible)
    QWidget.setTabOrder(chk_todo_visible, table)
    QWidget.setTabOrder(table, btn_prev)
    QWidget.setTabOrder(btn_prev, btn_next)
    return ConfirmacionesUIRefs(
        lbl_title=lbl_title,
        banner=banner,
        btn_ir_prediccion=btn_ir_prediccion,
        cmb_rango=cmb_rango,
        desde=desde,
        hasta=hasta,
        cmb_riesgo=cmb_riesgo,
        cmb_recordatorio=cmb_recordatorio,
        txt_buscar=txt_buscar,
        btn_actualizar=btn_actualizar,
        chk_todo_visible=chk_todo_visible,
        lbl_seleccionadas=lbl_seleccionadas,
        table=table,
        lbl_totales=lbl_totales,
        btn_prev=btn_prev,
        btn_next=btn_next,
        estado_pantalla=estado_pantalla,
        contenido_tabla=contenido_tabla,
    )

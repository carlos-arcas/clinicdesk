from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


@dataclass(slots=True)
class ConfirmacionesUIRefs:
    lbl_title: QLabel
    banner: QLabel
    btn_ir_prediccion: QPushButton
    cmb_rango: QComboBox
    desde: QDateEdit
    hasta: QDateEdit
    cmb_riesgo: QComboBox
    cmb_recordatorio: QComboBox
    txt_buscar: QLineEdit
    btn_actualizar: QPushButton
    chk_todo_visible: QCheckBox
    lbl_seleccionadas: QLabel
    table: QTableWidget
    lbl_totales: QLabel
    btn_prev: QPushButton
    btn_next: QPushButton
    estado_pantalla: EstadoPantallaWidget
    contenido_tabla: QWidget

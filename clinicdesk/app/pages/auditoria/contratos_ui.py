from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QTableWidget


@dataclass(slots=True)
class AuditoriaUIRefs:
    lbl_accesos_hoy: QLabel
    lbl_accesos_7_dias: QLabel
    lbl_top_acciones: QLabel
    combo_rango: QComboBox
    combo_accion: QComboBox
    combo_entidad: QComboBox
    input_usuario: QLineEdit
    input_desde: QLineEdit
    input_hasta: QLineEdit
    btn_buscar: QPushButton
    btn_limpiar: QPushButton
    tabla: QTableWidget
    lbl_estado: QLabel
    btn_reintentar: QPushButton
    btn_exportar: QPushButton
    btn_cargar_mas: QPushButton

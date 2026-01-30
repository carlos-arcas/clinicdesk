# app/ui/dialog_dispensar.py
"""
Diálogo para dispensar un medicamento desde una línea de receta.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.shared.selector_dialog import select_personal


@dataclass(slots=True)
class DispensarFormData:
    cantidad: int
    personal_id: int


class DispensarDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, *, container: AppContainer) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dispensar medicamento")
        self.setMinimumWidth(420)

        self._container = container
        self._personal_id: Optional[int] = None

        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 999999)
        self.spn_cantidad.setValue(1)

        self.txt_personal = QLineEdit()
        self.txt_personal.setReadOnly(True)
        self.btn_personal = QPushButton("Buscar…")
        self.btn_personal.clicked.connect(self._select_personal)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #b00020;")

        form = QFormLayout()
        form.addRow("Cantidad:", self.spn_cantidad)
        form.addRow("Personal (quien dispensa):", self._selector_row())

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Dispensar")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.lbl_error)
        layout.addLayout(btns)
        self.setLayout(layout)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_ok)

    def _selector_row(self) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(self.txt_personal, 1)
        row.addWidget(self.btn_personal)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _select_personal(self) -> None:
        selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._personal_id = selection.entity_id
        self.txt_personal.setText(selection.display)

    def _on_ok(self) -> None:
        if not self._personal_id:
            self.lbl_error.setText("Selecciona el personal que dispensa.")
            return
        self.accept()

    def get_data(self) -> Optional[DispensarFormData]:
        if self.result() != QDialog.Accepted:
            return None

        cantidad = int(self.spn_cantidad.value())
        return DispensarFormData(cantidad=cantidad, personal_id=int(self._personal_id or 0))

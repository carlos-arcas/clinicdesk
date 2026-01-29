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
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class DispensarFormData:
    cantidad: int
    personal_id: int


class DispensarDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dispensar medicamento")
        self.setMinimumWidth(420)

        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 999999)
        self.spn_cantidad.setValue(1)

        self.spn_personal = QSpinBox()
        self.spn_personal.setRange(1, 9999999)
        self.spn_personal.setValue(1)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #b00020;")

        form = QFormLayout()
        form.addRow("Cantidad:", self.spn_cantidad)
        form.addRow("Personal ID (quien dispensa):", self.spn_personal)

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
        self.btn_ok.clicked.connect(self.accept)

    def get_data(self) -> Optional[DispensarFormData]:
        if self.result() != QDialog.Accepted:
            return None

        cantidad = int(self.spn_cantidad.value())
        personal_id = int(self.spn_personal.value())
        return DispensarFormData(cantidad=cantidad, personal_id=personal_id)

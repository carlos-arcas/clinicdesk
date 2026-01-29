# app/ui/dialog_override.py
"""
Diálogo genérico de confirmación consciente (override).

Uso:
- Se muestra cuando un usecase devuelve warnings o lanza PendingWarningsError.
- Obliga a introducir nota_override.
- Obliga a introducir confirmado_por_personal_id.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class OverrideDecision:
    accepted: bool
    nota_override: Optional[str]
    confirmado_por_personal_id: Optional[int]


class OverrideDialog(QDialog):
    def __init__(self, parent: Optional[QWidget], *, title: str, warnings: List[object]) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(720)

        self._warnings = warnings

        self.lbl_info = QLabel(
            "Se han detectado advertencias.\n"
            "Para continuar es obligatorio justificar el motivo y confirmar con un ID de personal."
        )

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["Severidad", "Código", "Mensaje"])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self._render_warnings()

        self.txt_nota = QTextEdit()
        self.txt_nota.setPlaceholderText("Nota obligatoria… (Ej: 'He cambiado el turno con Clara', 'No está subido el cuadrante aún', etc.)")

        self.spn_confirmador = QSpinBox()
        self.spn_confirmador.setRange(0, 9999999)
        self.spn_confirmador.setValue(0)

        row_confirm = QHBoxLayout()
        row_confirm.addWidget(QLabel("Confirmado por personal ID:"))
        row_confirm.addWidget(self.spn_confirmador)
        row_confirm.addStretch(1)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_accept = QPushButton("Guardar igualmente")

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_accept)

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_info)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Advertencias:"))
        layout.addWidget(self.tbl)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Nota de override (obligatoria):"))
        layout.addWidget(self.txt_nota)
        layout.addLayout(row_confirm)
        layout.addLayout(btns)

        self.setLayout(layout)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_accept.clicked.connect(self._on_accept)

    def _render_warnings(self) -> None:
        self.tbl.setRowCount(0)
        for w in self._warnings:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            sev = getattr(w, "severidad", "")
            code = getattr(w, "codigo", "")
            msg = getattr(w, "mensaje", "")

            self.tbl.setItem(r, 0, QTableWidgetItem(str(sev)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(code)))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(msg)))

        self.tbl.resizeColumnsToContents()

    def _on_accept(self) -> None:
        nota = (self.txt_nota.toPlainText() or "").strip()
        confirmador = int(self.spn_confirmador.value())

        if not nota:
            self.lbl_info.setText("Falta la nota obligatoria. No se puede continuar.")
            return
        if confirmador <= 0:
            self.lbl_info.setText("Falta el ID del personal que confirma. No se puede continuar.")
            return

        self.accept()

    def get_decision(self) -> OverrideDecision:
        if self.result() != QDialog.Accepted:
            return OverrideDecision(False, None, None)

        return OverrideDecision(
            accepted=True,
            nota_override=(self.txt_nota.toPlainText() or "").strip(),
            confirmado_por_personal_id=int(self.spn_confirmador.value()),
        )

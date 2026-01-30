# app/ui/dialog_override.py
"""
Diálogo genérico de confirmación consciente (override).

Uso:
- Se muestra cuando un usecase devuelve warnings o lanza PendingWarningsError.
- Obliga a introducir nota_override.
 - Obliga a seleccionar quién confirma.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.shared.selector_dialog import select_personal


@dataclass(slots=True)
class OverrideDecision:
    accepted: bool
    nota_override: Optional[str]
    confirmado_por_personal_id: Optional[int]


class OverrideDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        *,
        title: str,
        warnings: List[object],
        container: Optional[AppContainer] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(720)

        self._warnings = warnings
        self._container = container
        self._confirmador_id: Optional[int] = None

        self.lbl_info = QLabel(
            "Se han detectado advertencias.\n"
            "Para continuar es obligatorio justificar el motivo y confirmar con personal."
        )

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["Severidad", "Código", "Mensaje"])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self._render_warnings()

        self.txt_nota = QTextEdit()
        self.txt_nota.setPlaceholderText("Nota obligatoria… (Ej: 'He cambiado el turno con Clara', 'No está subido el cuadrante aún', etc.)")

        self.txt_confirmador = QLineEdit()
        self.txt_confirmador.setReadOnly(True)
        self.btn_confirmador = QPushButton("Buscar personal…")
        self.btn_confirmador.clicked.connect(self._select_confirmador)

        row_confirm = QHBoxLayout()
        row_confirm.addWidget(QLabel("Confirmado por:"))
        row_confirm.addWidget(self.txt_confirmador, 1)
        row_confirm.addWidget(self.btn_confirmador)
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

        if not nota:
            self.lbl_info.setText("Falta la nota obligatoria. No se puede continuar.")
            return
        if not self._confirmador_id:
            self.lbl_info.setText("Falta seleccionar el personal que confirma. No se puede continuar.")
            return

        self.accept()

    def get_decision(self) -> OverrideDecision:
        if self.result() != QDialog.Accepted:
            return OverrideDecision(False, None, None)

        return OverrideDecision(
            accepted=True,
            nota_override=(self.txt_nota.toPlainText() or "").strip(),
            confirmado_por_personal_id=int(self._confirmador_id or 0),
        )

    def _select_confirmador(self) -> None:
        if not self._container:
            self.lbl_info.setText("No hay datos de personal disponibles para seleccionar.")
            return
        selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._confirmador_id = selection.entity_id
        self.txt_confirmador.setText(selection.display)

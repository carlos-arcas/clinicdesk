# app/ui/dialog_cita_form.py
"""
Formulario de cita (crear).

Campos:
- selección de paciente, médico y sala
- inicio, fin (ISO)
- motivo, observaciones
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.shared.selector_dialog import (
    select_medico,
    select_paciente,
    select_sala,
)


@dataclass(slots=True)
class CitaFormData:
    paciente_id: int
    medico_id: int
    sala_id: int
    inicio: str
    fin: str
    motivo: Optional[str]
    observaciones: Optional[str]


class CitaFormDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        default_date: str,
        container: AppContainer,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nueva cita")
        self.setMinimumWidth(520)

        self._container = container
        self._paciente_id: Optional[int] = None
        self._medico_id: Optional[int] = None
        self._sala_id: Optional[int] = None

        self.ed_paciente = QLineEdit()
        self.ed_paciente.setReadOnly(True)
        self.btn_paciente = QPushButton("Buscar…")
        self.btn_paciente.clicked.connect(self._select_paciente)

        self.ed_medico = QLineEdit()
        self.ed_medico.setReadOnly(True)
        self.btn_medico = QPushButton("Buscar…")
        self.btn_medico.clicked.connect(self._select_medico)

        self.ed_sala = QLineEdit()
        self.ed_sala.setReadOnly(True)
        self.btn_sala = QPushButton("Buscar…")
        self.btn_sala.clicked.connect(self._select_sala)

        self.ed_inicio = QLineEdit()
        self.ed_fin = QLineEdit()

        self.ed_inicio.setText(f"{default_date} 09:00:00")
        self.ed_fin.setText(f"{default_date} 09:30:00")

        self.ed_motivo = QLineEdit()
        self.ed_obs = QTextEdit()

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #b00020;")

        form = QFormLayout()
        form.addRow("Paciente:", self._build_selector_row(self.ed_paciente, self.btn_paciente))
        form.addRow("Médico:", self._build_selector_row(self.ed_medico, self.btn_medico))
        form.addRow("Sala:", self._build_selector_row(self.ed_sala, self.btn_sala))
        form.addRow("Inicio (YYYY-MM-DD HH:MM:SS):", self.ed_inicio)
        form.addRow("Fin (YYYY-MM-DD HH:MM:SS):", self.ed_fin)
        form.addRow("Motivo:", self.ed_motivo)
        form.addRow("Observaciones:", self.ed_obs)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Crear")

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

    @staticmethod
    def _build_selector_row(field: QLineEdit, button: QPushButton) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(field, 1)
        row.addWidget(button)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _select_paciente(self) -> None:
        selection = select_paciente(self, self._container.connection)
        if not selection:
            return
        self._paciente_id = selection.entity_id
        self.ed_paciente.setText(selection.display)

    def _select_medico(self) -> None:
        selection = select_medico(self, self._container.connection)
        if not selection:
            return
        self._medico_id = selection.entity_id
        self.ed_medico.setText(selection.display)

    def _select_sala(self) -> None:
        selection = select_sala(self, self._container.connection)
        if not selection:
            return
        self._sala_id = selection.entity_id
        self.ed_sala.setText(selection.display)

    def _on_ok(self) -> None:
        if not self._paciente_id or not self._medico_id or not self._sala_id:
            self.lbl_error.setText("Selecciona paciente, médico y sala.")
            return

        if not (self.ed_inicio.text().strip() and self.ed_fin.text().strip()):
            self.lbl_error.setText("Inicio y fin son obligatorios.")
            return

        self.accept()

    def get_data(self) -> Optional[CitaFormData]:
        if self.result() != QDialog.Accepted:
            return None

        return CitaFormData(
            paciente_id=int(self._paciente_id or 0),
            medico_id=int(self._medico_id or 0),
            sala_id=int(self._sala_id or 0),
            inicio=self.ed_inicio.text().strip(),
            fin=self.ed_fin.text().strip(),
            motivo=(self.ed_motivo.text() or "").strip() or None,
            observaciones=(self.ed_obs.toPlainText() or "").strip() or None,
        )

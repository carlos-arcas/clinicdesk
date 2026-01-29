# app/ui/dialog_cita_form.py
"""
Formulario de cita (crear).

Campos:
- paciente_id, medico_id, sala_id
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
    def __init__(self, parent: Optional[QWidget] = None, *, default_date: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nueva cita")
        self.setMinimumWidth(520)

        # Inputs (texto simple para empezar; luego se cambia por combos y datetime widgets)
        self.ed_paciente = QLineEdit()
        self.ed_medico = QLineEdit()
        self.ed_sala = QLineEdit()

        self.ed_inicio = QLineEdit()
        self.ed_fin = QLineEdit()

        self.ed_inicio.setText(f"{default_date} 09:00:00")
        self.ed_fin.setText(f"{default_date} 09:30:00")

        self.ed_motivo = QLineEdit()
        self.ed_obs = QTextEdit()

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #b00020;")

        form = QFormLayout()
        form.addRow("Paciente ID:", self.ed_paciente)
        form.addRow("Médico ID:", self.ed_medico)
        form.addRow("Sala ID:", self.ed_sala)
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

    def _on_ok(self) -> None:
        # Validación mínima de UI (lo serio lo hace el usecase)
        try:
            int(self.ed_paciente.text().strip())
            int(self.ed_medico.text().strip())
            int(self.ed_sala.text().strip())
        except ValueError:
            self.lbl_error.setText("Paciente/Médico/Sala deben ser enteros.")
            return

        if not (self.ed_inicio.text().strip() and self.ed_fin.text().strip()):
            self.lbl_error.setText("Inicio y fin son obligatorios.")
            return

        self.accept()

    def get_data(self) -> Optional[CitaFormData]:
        if self.result() != QDialog.Accepted:
            return None

        return CitaFormData(
            paciente_id=int(self.ed_paciente.text().strip()),
            medico_id=int(self.ed_medico.text().strip()),
            sala_id=int(self.ed_sala.text().strip()),
            inicio=self.ed_inicio.text().strip(),
            fin=self.ed_fin.text().strip(),
            motivo=(self.ed_motivo.text() or "").strip() or None,
            observaciones=(self.ed_obs.toPlainText() or "").strip() or None,
        )

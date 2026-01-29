from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QWidget,
)

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente


@dataclass(slots=True)
class PacienteFormData:
    paciente: Paciente


class PacienteFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paciente")
        self._paciente_id: Optional[int] = None

        self.cbo_tipo_documento = QComboBox()
        self.cbo_tipo_documento.addItems([t.value for t in TipoDocumento])

        self.txt_documento = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_apellidos = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_fecha_nacimiento = QLineEdit()
        self.txt_direccion = QLineEdit()
        self.txt_num_historia = QLineEdit()
        self.txt_alergias = QTextEdit()
        self.txt_observaciones = QTextEdit()
        self.chk_activo = QCheckBox("Activo")
        self.chk_activo.setChecked(True)

        form = QFormLayout()
        form.addRow("Tipo documento", self.cbo_tipo_documento)
        form.addRow("Documento", self.txt_documento)
        form.addRow("Nombre", self.txt_nombre)
        form.addRow("Apellidos", self.txt_apellidos)
        form.addRow("Teléfono", self.txt_telefono)
        form.addRow("Email", self.txt_email)
        form.addRow("Fecha nacimiento (YYYY-MM-DD)", self.txt_fecha_nacimiento)
        form.addRow("Dirección", self.txt_direccion)
        form.addRow("Nº historia", self.txt_num_historia)
        form.addRow("Alergias", self.txt_alergias)
        form.addRow("Observaciones", self.txt_observaciones)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_paciente(self, paciente: Paciente) -> None:
        self._paciente_id = paciente.id
        self.cbo_tipo_documento.setCurrentText(paciente.tipo_documento.value)
        self.txt_documento.setText(paciente.documento)
        self.txt_nombre.setText(paciente.nombre)
        self.txt_apellidos.setText(paciente.apellidos)
        self.txt_telefono.setText(paciente.telefono or "")
        self.txt_email.setText(paciente.email or "")
        self.txt_fecha_nacimiento.setText(
            paciente.fecha_nacimiento.isoformat() if paciente.fecha_nacimiento else ""
        )
        self.txt_direccion.setText(paciente.direccion or "")
        self.txt_num_historia.setText(paciente.num_historia or "")
        self.txt_alergias.setPlainText(paciente.alergias or "")
        self.txt_observaciones.setPlainText(paciente.observaciones or "")
        self.chk_activo.setChecked(paciente.activo)

    def get_data(self) -> Optional[PacienteFormData]:
        try:
            fecha = self.txt_fecha_nacimiento.text().strip()
            fecha_dt = date.fromisoformat(fecha) if fecha else None

            paciente = Paciente(
                id=self._paciente_id,
                tipo_documento=TipoDocumento(self.cbo_tipo_documento.currentText()),
                documento=self.txt_documento.text().strip(),
                nombre=self.txt_nombre.text().strip(),
                apellidos=self.txt_apellidos.text().strip(),
                telefono=self.txt_telefono.text().strip() or None,
                email=self.txt_email.text().strip() or None,
                fecha_nacimiento=fecha_dt,
                direccion=self.txt_direccion.text().strip() or None,
                activo=self.chk_activo.isChecked(),
                num_historia=self.txt_num_historia.text().strip() or None,
                alergias=self.txt_alergias.toPlainText().strip() or None,
                observaciones=self.txt_observaciones.toPlainText().strip() or None,
            )
            paciente.validar()
        except (ValueError, ValidationError) as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return None

        return PacienteFormData(paciente=paciente)

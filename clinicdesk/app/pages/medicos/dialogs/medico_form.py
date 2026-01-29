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
    QWidget,
)

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Medico


@dataclass(slots=True)
class MedicoFormData:
    medico: Medico


class MedicoFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Médico")
        self._medico_id: Optional[int] = None

        self.cbo_tipo_documento = QComboBox()
        self.cbo_tipo_documento.addItems([t.value for t in TipoDocumento])

        self.txt_documento = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_apellidos = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_fecha_nacimiento = QLineEdit()
        self.txt_direccion = QLineEdit()
        self.txt_num_colegiado = QLineEdit()
        self.txt_especialidad = QLineEdit()
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
        form.addRow("Nº colegiado", self.txt_num_colegiado)
        form.addRow("Especialidad", self.txt_especialidad)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_medico(self, medico: Medico) -> None:
        self._medico_id = medico.id
        self.cbo_tipo_documento.setCurrentText(medico.tipo_documento.value)
        self.txt_documento.setText(medico.documento)
        self.txt_nombre.setText(medico.nombre)
        self.txt_apellidos.setText(medico.apellidos)
        self.txt_telefono.setText(medico.telefono or "")
        self.txt_email.setText(medico.email or "")
        self.txt_fecha_nacimiento.setText(
            medico.fecha_nacimiento.isoformat() if medico.fecha_nacimiento else ""
        )
        self.txt_direccion.setText(medico.direccion or "")
        self.txt_num_colegiado.setText(medico.num_colegiado)
        self.txt_especialidad.setText(medico.especialidad)
        self.chk_activo.setChecked(medico.activo)

    def get_data(self) -> Optional[MedicoFormData]:
        try:
            fecha = self.txt_fecha_nacimiento.text().strip()
            fecha_dt = date.fromisoformat(fecha) if fecha else None

            medico = Medico(
                id=self._medico_id,
                tipo_documento=TipoDocumento(self.cbo_tipo_documento.currentText()),
                documento=self.txt_documento.text().strip(),
                nombre=self.txt_nombre.text().strip(),
                apellidos=self.txt_apellidos.text().strip(),
                telefono=self.txt_telefono.text().strip() or None,
                email=self.txt_email.text().strip() or None,
                fecha_nacimiento=fecha_dt,
                direccion=self.txt_direccion.text().strip() or None,
                activo=self.chk_activo.isChecked(),
                num_colegiado=self.txt_num_colegiado.text().strip(),
                especialidad=self.txt_especialidad.text().strip(),
            )
            medico.validar()
        except (ValueError, ValidationError) as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return None

        return MedicoFormData(medico=medico)

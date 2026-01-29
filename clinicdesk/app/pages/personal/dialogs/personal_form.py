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
from clinicdesk.app.domain.modelos import Personal


@dataclass(slots=True)
class PersonalFormData:
    personal: Personal


class PersonalFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Personal")
        self._personal_id: Optional[int] = None

        self.cbo_tipo_documento = QComboBox()
        self.cbo_tipo_documento.addItems([t.value for t in TipoDocumento])

        self.txt_documento = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_apellidos = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_fecha_nacimiento = QLineEdit()
        self.txt_direccion = QLineEdit()
        self.txt_puesto = QLineEdit()
        self.txt_turno = QLineEdit()
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
        form.addRow("Puesto", self.txt_puesto)
        form.addRow("Turno", self.txt_turno)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_personal(self, personal: Personal) -> None:
        self._personal_id = personal.id
        self.cbo_tipo_documento.setCurrentText(personal.tipo_documento.value)
        self.txt_documento.setText(personal.documento)
        self.txt_nombre.setText(personal.nombre)
        self.txt_apellidos.setText(personal.apellidos)
        self.txt_telefono.setText(personal.telefono or "")
        self.txt_email.setText(personal.email or "")
        self.txt_fecha_nacimiento.setText(
            personal.fecha_nacimiento.isoformat() if personal.fecha_nacimiento else ""
        )
        self.txt_direccion.setText(personal.direccion or "")
        self.txt_puesto.setText(personal.puesto)
        self.txt_turno.setText(personal.turno or "")
        self.chk_activo.setChecked(personal.activo)

    def get_data(self) -> Optional[PersonalFormData]:
        try:
            fecha = self.txt_fecha_nacimiento.text().strip()
            fecha_dt = date.fromisoformat(fecha) if fecha else None

            personal = Personal(
                id=self._personal_id,
                tipo_documento=TipoDocumento(self.cbo_tipo_documento.currentText()),
                documento=self.txt_documento.text().strip(),
                nombre=self.txt_nombre.text().strip(),
                apellidos=self.txt_apellidos.text().strip(),
                telefono=self.txt_telefono.text().strip() or None,
                email=self.txt_email.text().strip() or None,
                fecha_nacimiento=fecha_dt,
                direccion=self.txt_direccion.text().strip() or None,
                activo=self.chk_activo.isChecked(),
                puesto=self.txt_puesto.text().strip(),
                turno=self.txt_turno.text().strip() or None,
            )
            personal.validar()
        except (ValueError, ValidationError) as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return None

        return PersonalFormData(personal=personal)

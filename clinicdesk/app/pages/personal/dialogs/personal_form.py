from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QDate, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QWidget,
)

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Personal
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.label_utils import required_label


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
        self.date_fecha_nacimiento = QDateEdit()
        self.date_fecha_nacimiento.setDisplayFormat("yyyy-MM-dd")
        self.date_fecha_nacimiento.setCalendarPopup(True)
        self.date_fecha_nacimiento.setDate(QDate.currentDate())
        self.chk_sin_fecha = QCheckBox("Sin fecha")
        self.chk_sin_fecha.setChecked(True)
        self.chk_sin_fecha.toggled.connect(self._toggle_fecha_nacimiento)
        self._toggle_fecha_nacimiento(True)
        self.txt_direccion = QLineEdit()
        self.txt_puesto = QLineEdit()
        self.txt_turno = QLineEdit()
        self.chk_activo = QCheckBox("Registro activo")
        self.chk_activo.setChecked(True)
        self.chk_activo.setToolTip("Si se desmarca, el registro quedará inactivo y oculto en filtros de activos.")

        form = QFormLayout()
        form.addRow(required_label("Tipo documento"), self.cbo_tipo_documento)
        form.addRow(required_label("Documento"), self.txt_documento)
        form.addRow(required_label("Nombre"), self.txt_nombre)
        form.addRow(required_label("Apellidos"), self.txt_apellidos)
        form.addRow("Teléfono", self.txt_telefono)
        form.addRow("Email", self.txt_email)
        fecha_layout = QHBoxLayout()
        fecha_layout.addWidget(self.date_fecha_nacimiento)
        fecha_layout.addWidget(self.chk_sin_fecha)
        fecha_widget = QWidget()
        fecha_widget.setLayout(fecha_layout)
        form.addRow("Fecha nacimiento", fecha_widget)
        form.addRow("Dirección", self.txt_direccion)
        form.addRow(required_label("Puesto"), self.txt_puesto)
        form.addRow("Turno", self.txt_turno)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
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
        if personal.fecha_nacimiento:
            self.date_fecha_nacimiento.setDate(
                QDate(
                    personal.fecha_nacimiento.year,
                    personal.fecha_nacimiento.month,
                    personal.fecha_nacimiento.day,
                )
            )
            self.chk_sin_fecha.setChecked(False)
        else:
            self.chk_sin_fecha.setChecked(True)
        self.txt_direccion.setText(personal.direccion or "")
        self.txt_puesto.setText(personal.puesto)
        self.txt_turno.setText(personal.turno or "")
        self.chk_activo.setChecked(personal.activo)

    def get_data(self) -> Optional[PersonalFormData]:
        try:
            fecha_dt = None
            if not self.chk_sin_fecha.isChecked():
                fecha_dt = self.date_fecha_nacimiento.date().toPython()

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
            self._highlight_for_error(exc)
            present_error(self, exc)
            return None

        return PersonalFormData(personal=personal)

    def _toggle_fecha_nacimiento(self, checked: bool) -> None:
        self.date_fecha_nacimiento.setEnabled(not checked)

    def _mark_invalid(self, widget: QWidget) -> None:
        widget.setStyleSheet("border: 1px solid #d9534f;")
        QTimer.singleShot(2500, lambda: widget.setStyleSheet(""))

    def _highlight_for_error(self, exc: Exception) -> None:
        message = str(exc).lower()
        if "documento" in message:
            self._mark_invalid(self.txt_documento)
        elif "nombre" in message and "apellidos" not in message:
            self._mark_invalid(self.txt_nombre)
        elif "apellidos" in message:
            self._mark_invalid(self.txt_apellidos)
        elif "teléfono" in message or "telefono" in message:
            self._mark_invalid(self.txt_telefono)
        elif "email" in message:
            self._mark_invalid(self.txt_email)
        elif "fecha" in message:
            self._mark_invalid(self.date_fecha_nacimiento)

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
    QTextEdit,
    QWidget,
)

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.label_utils import required_label


@dataclass(slots=True)
class PacienteFormData:
    paciente: Paciente


class PacienteFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Paciente")
        self._paciente_id: Optional[int] = None
        self._num_historia: Optional[str] = None

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
        self.txt_num_historia = QLineEdit()
        self.txt_num_historia.setReadOnly(True)
        self.txt_num_historia.setPlaceholderText("Se genera automáticamente")
        self.txt_alergias = QTextEdit()
        self.txt_observaciones = QTextEdit()
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
        form.addRow("Nº historia", self.txt_num_historia)
        form.addRow("Alergias", self.txt_alergias)
        form.addRow("Observaciones", self.txt_observaciones)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_paciente(self, paciente: Paciente) -> None:
        self._paciente_id = paciente.id
        self._num_historia = paciente.num_historia
        self.cbo_tipo_documento.setCurrentText(paciente.tipo_documento.value)
        self.txt_documento.setText(paciente.documento)
        self.txt_nombre.setText(paciente.nombre)
        self.txt_apellidos.setText(paciente.apellidos)
        self.txt_telefono.setText(paciente.telefono or "")
        self.txt_email.setText(paciente.email or "")
        if paciente.fecha_nacimiento:
            self.date_fecha_nacimiento.setDate(
                QDate(
                    paciente.fecha_nacimiento.year,
                    paciente.fecha_nacimiento.month,
                    paciente.fecha_nacimiento.day,
                )
            )
            self.chk_sin_fecha.setChecked(False)
        else:
            self.chk_sin_fecha.setChecked(True)
        self.txt_direccion.setText(paciente.direccion or "")
        self.txt_num_historia.setText(paciente.num_historia or "")
        self.txt_alergias.setPlainText(paciente.alergias or "")
        self.txt_observaciones.setPlainText(paciente.observaciones or "")
        self.chk_activo.setChecked(paciente.activo)

    def get_data(self) -> Optional[PacienteFormData]:
        try:
            fecha_dt = None
            if not self.chk_sin_fecha.isChecked():
                fecha_dt = self.date_fecha_nacimiento.date().toPython()

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
                num_historia=self._num_historia,
                alergias=self.txt_alergias.toPlainText().strip() or None,
                observaciones=self.txt_observaciones.toPlainText().strip() or None,
            )
            paciente.validar()
        except (ValueError, ValidationError) as exc:
            self._highlight_for_error(exc)
            present_error(self, exc)
            return None

        return PacienteFormData(paciente=paciente)

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

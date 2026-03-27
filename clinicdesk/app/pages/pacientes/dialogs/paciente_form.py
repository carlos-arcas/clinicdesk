from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.formularios_validacion import (
    primer_campo_con_error,
    validar_formulario_paciente,
)
from clinicdesk.app.ui.forms_estado import ControladorEstadoFormulario
from clinicdesk.app.ui.label_utils import required_label


@dataclass(slots=True)
class PacienteFormData:
    paciente: Paciente


class PacienteFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, *, i18n: I18nManager | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n or I18nManager("es")
        self.setWindowTitle(self._i18n.t("pacientes.form.title"))
        self._paciente_id: Optional[int] = None
        self._num_historia: Optional[str] = None
        self._submit_en_curso = False
        self._control_estado = ControladorEstadoFormulario(validador=self._validar_campos)

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
        self.chk_sin_fecha = QCheckBox(self._i18n.t("form.sin_fecha"))
        self.chk_sin_fecha.setChecked(True)
        self.chk_sin_fecha.toggled.connect(self._toggle_fecha_nacimiento)
        self._toggle_fecha_nacimiento(True)
        self.txt_direccion = QLineEdit()
        self.txt_num_historia = QLineEdit()
        self.txt_num_historia.setReadOnly(True)
        self.txt_num_historia.setPlaceholderText(self._i18n.t("pacientes.form.historia.auto"))
        self.txt_alergias = QTextEdit()
        self.txt_observaciones = QTextEdit()
        self.chk_activo = QCheckBox(self._i18n.t("form.registro_activo"))
        self.chk_activo.setChecked(True)
        self.chk_activo.setToolTip(self._i18n.t("form.registro_activo.tooltip"))

        self._labels_error: dict[str, QLabel] = {}
        form = QFormLayout()
        form.addRow(required_label(self._i18n.t("form.tipo_documento")), self.cbo_tipo_documento)
        form.addRow(
            required_label(self._i18n.t("form.documento")), self._campo_con_error("documento", self.txt_documento)
        )
        form.addRow(required_label(self._i18n.t("form.nombre")), self._campo_con_error("nombre", self.txt_nombre))
        form.addRow(
            required_label(self._i18n.t("form.apellidos")), self._campo_con_error("apellidos", self.txt_apellidos)
        )
        form.addRow(self._i18n.t("form.telefono"), self._campo_con_error("telefono", self.txt_telefono))
        form.addRow(self._i18n.t("form.email"), self._campo_con_error("email", self.txt_email))
        fecha_layout = QHBoxLayout()
        fecha_layout.addWidget(self.date_fecha_nacimiento)
        fecha_layout.addWidget(self.chk_sin_fecha)
        fecha_widget = QWidget()
        fecha_widget.setLayout(fecha_layout)
        form.addRow(self._i18n.t("form.fecha_nacimiento"), fecha_widget)
        form.addRow(self._i18n.t("form.direccion"), self.txt_direccion)
        form.addRow(self._i18n.t("pacientes.form.historia"), self.txt_num_historia)
        form.addRow(self._i18n.t("pacientes.form.alergias"), self.txt_alergias)
        form.addRow(self._i18n.t("pacientes.form.observaciones"), self.txt_observaciones)
        form.addRow("", self.chk_activo)

        self.lbl_error_general = QLabel("")
        self.lbl_error_general.setStyleSheet("color: #b00020;")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self._btn_guardar = buttons.button(QDialogButtonBox.Save)
        self._btn_cancelar = buttons.button(QDialogButtonBox.Cancel)
        self._btn_guardar.setText(self._i18n.t("comun.guardar"))
        self._btn_cancelar.setText(self._i18n.t("comun.cancelar"))
        self._btn_guardar.clicked.connect(self._on_guardar_click)
        self._btn_cancelar.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.lbl_error_general)
        layout.addWidget(buttons)

        self._bind_estado()
        self._control_estado.inicializar(self._snapshot_formulario())
        self._aplicar_estado()
        self.txt_documento.setFocus()

    def _campo_con_error(self, clave: str, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel("")
        label.setStyleSheet("color: #b00020;")
        label.setVisible(False)
        self._labels_error[clave] = label
        layout.addWidget(widget)
        layout.addWidget(label)
        return wrapper

    def _bind_estado(self) -> None:
        self.txt_documento.textChanged.connect(lambda _: self._on_campo_cambiado("documento"))
        self.txt_nombre.textChanged.connect(lambda _: self._on_campo_cambiado("nombre"))
        self.txt_apellidos.textChanged.connect(lambda _: self._on_campo_cambiado("apellidos"))
        self.txt_telefono.textChanged.connect(lambda _: self._on_campo_cambiado("telefono"))
        self.txt_email.textChanged.connect(lambda _: self._on_campo_cambiado("email"))
        self.txt_direccion.textChanged.connect(lambda _: self._on_campo_cambiado("direccion"))
        self.txt_alergias.textChanged.connect(lambda: self._on_campo_cambiado("alergias"))
        self.txt_observaciones.textChanged.connect(lambda: self._on_campo_cambiado("observaciones"))
        self.chk_sin_fecha.toggled.connect(lambda _: self._on_campo_cambiado("sin_fecha"))
        self.date_fecha_nacimiento.dateChanged.connect(lambda _: self._on_campo_cambiado("fecha_nacimiento"))
        self.cbo_tipo_documento.currentTextChanged.connect(lambda _: self._on_campo_cambiado("tipo_documento"))

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
                QDate(paciente.fecha_nacimiento.year, paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day)
            )
            self.chk_sin_fecha.setChecked(False)
        else:
            self.chk_sin_fecha.setChecked(True)
        self.txt_direccion.setText(paciente.direccion or "")
        self.txt_num_historia.setText(paciente.num_historia or "")
        self.txt_alergias.setPlainText(paciente.alergias or "")
        self.txt_observaciones.setPlainText(paciente.observaciones or "")
        self.chk_activo.setChecked(paciente.activo)
        self._control_estado.inicializar(self._snapshot_formulario())
        self._aplicar_estado()

    def _on_campo_cambiado(self, _: str) -> None:
        self._control_estado.actualizar_valores(self._snapshot_formulario())
        self._control_estado.limpiar_error_guardado()
        self._aplicar_estado()

    def _snapshot_formulario(self) -> dict[str, str]:
        return {
            "tipo_documento": self.cbo_tipo_documento.currentText().strip(),
            "documento": self.txt_documento.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "apellidos": self.txt_apellidos.text().strip(),
            "telefono": self.txt_telefono.text().strip(),
            "email": self.txt_email.text().strip(),
            "direccion": self.txt_direccion.text().strip(),
            "alergias": self.txt_alergias.toPlainText().strip(),
            "observaciones": self.txt_observaciones.toPlainText().strip(),
            "sin_fecha": "1" if self.chk_sin_fecha.isChecked() else "0",
            "fecha_nacimiento": self.date_fecha_nacimiento.date().toString("yyyy-MM-dd"),
        }

    def _validar_campos(self, valores: dict[str, str]) -> dict[str, str]:
        return validar_formulario_paciente(valores, i18n=self._i18n)

    def _aplicar_estado(self) -> None:
        estado = self._control_estado.estado
        self._btn_guardar.setEnabled(estado.listo_para_enviar and not self._submit_en_curso)
        self._btn_guardar.setText(self._i18n.t("form.guardando") if estado.guardando else self._i18n.t("comun.guardar"))
        self.lbl_error_general.setText(estado.error_guardado or "")
        for clave, label in self._labels_error.items():
            mensaje = estado.errores_validacion.get(clave, "")
            label.setText(mensaje)
            label.setVisible(bool(mensaje))

    def _on_guardar_click(self) -> None:
        if self._submit_en_curso:
            return
        self._control_estado.actualizar_valores(self._snapshot_formulario())
        estado = self._control_estado.validar()
        self._aplicar_estado()
        if not estado.valido:
            self._enfocar_primer_error(estado.errores_validacion)
            return
        self._submit_en_curso = True
        self._control_estado.marcar_guardando(True)
        self._aplicar_estado()
        self.accept()

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
            self._submit_en_curso = False
            self._control_estado.marcar_guardando(False)
            self._control_estado.registrar_error_guardado(self._i18n.t("form.error.revisar_campos"))
            self._aplicar_estado()
            present_error(self, exc)
            return None

        self._control_estado.marcar_guardado_exitoso()
        return PacienteFormData(paciente=paciente)

    def reject(self) -> None:
        self._control_estado.actualizar_valores(self._snapshot_formulario(), validar=False)
        if self._control_estado.estado.cambios_sin_guardar and not self._confirmar_descartar():
            return
        super().reject()

    def _confirmar_descartar(self) -> bool:
        respuesta = QMessageBox.question(
            self,
            self._i18n.t("form.unsaved.title"),
            self._i18n.t("form.unsaved.message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return respuesta == QMessageBox.Yes

    def _toggle_fecha_nacimiento(self, checked: bool) -> None:
        self.date_fecha_nacimiento.setEnabled(not checked)

    def _enfocar_primer_error(self, errores: dict[str, str]) -> None:
        widgets_por_campo = {
            "documento": self.txt_documento,
            "nombre": self.txt_nombre,
            "apellidos": self.txt_apellidos,
            "telefono": self.txt_telefono,
            "email": self.txt_email,
        }
        campo = primer_campo_con_error(errores, tuple(widgets_por_campo.keys()))
        if campo:
            widgets_por_campo[campo].setFocus()

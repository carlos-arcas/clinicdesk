from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.shared.selector_dialog import select_medico, select_paciente, select_sala
from clinicdesk.app.ui.formularios_validacion import (
    primer_campo_con_error,
    validar_formulario_cita,
)
from clinicdesk.app.ui.forms_estado import ControladorEstadoFormulario
from clinicdesk.app.ui.label_utils import required_label


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
    def __init__(self, parent: Optional[QWidget] = None, *, default_date: str, container: AppContainer) -> None:
        super().__init__(parent)
        self._i18n = I18nManager("es")
        self.setWindowTitle(self._i18n.t("citas.form.title"))
        self.setMinimumWidth(520)

        self._container = container
        self._paciente_id: Optional[int] = None
        self._medico_id: Optional[int] = None
        self._sala_id: Optional[int] = None
        self._submit_en_curso = False
        self._control_estado = ControladorEstadoFormulario(validador=self._validar_campos)

        self.ed_paciente = QLineEdit()
        self.ed_paciente.setReadOnly(True)
        self.btn_paciente = QPushButton(self._i18n.t("comun.buscar"))
        self.btn_paciente.clicked.connect(self._select_paciente)

        self.ed_medico = QLineEdit()
        self.ed_medico.setReadOnly(True)
        self.btn_medico = QPushButton(self._i18n.t("comun.buscar"))
        self.btn_medico.clicked.connect(self._select_medico)

        self.ed_sala = QLineEdit()
        self.ed_sala.setReadOnly(True)
        self.btn_sala = QPushButton(self._i18n.t("comun.buscar"))
        self.btn_sala.clicked.connect(self._select_sala)

        self.ed_inicio = QLineEdit(f"{default_date} 09:00:00")
        self.ed_fin = QLineEdit(f"{default_date} 09:30:00")
        self.ed_motivo = QLineEdit()
        self.ed_obs = QTextEdit()

        self._labels_error: dict[str, QLabel] = {}
        form = QFormLayout()
        form.addRow(required_label(self._i18n.t("form.paciente")), self._build_selector_row(self.ed_paciente, self.btn_paciente))
        form.addRow(required_label(self._i18n.t("form.medico")), self._build_selector_row(self.ed_medico, self.btn_medico))
        form.addRow(required_label(self._i18n.t("form.sala")), self._build_selector_row(self.ed_sala, self.btn_sala))
        form.addRow(required_label(self._i18n.t("form.inicio")), self._campo_con_error("inicio", self.ed_inicio))
        form.addRow(required_label(self._i18n.t("form.fin")), self._campo_con_error("fin", self.ed_fin))
        form.addRow(self._i18n.t("citas.form.motivo"), self.ed_motivo)
        form.addRow(self._i18n.t("citas.form.observaciones"), self.ed_obs)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #b00020;")

        self.btn_cancel = QPushButton(self._i18n.t("comun.cancelar"))
        self.btn_ok = QPushButton(self._i18n.t("citas.form.crear"))
        self.btn_ok.setDefault(True)
        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.lbl_error)
        layout.addLayout(btns)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_ok)
        self.ed_inicio.textChanged.connect(self._on_form_changed)
        self.ed_fin.textChanged.connect(self._on_form_changed)
        self.ed_motivo.textChanged.connect(self._on_form_changed)
        self.ed_obs.textChanged.connect(self._on_form_changed)

        self._control_estado.inicializar(self._snapshot_formulario())
        self._control_estado.validar()
        self._aplicar_estado()

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

    @staticmethod
    def _build_selector_row(field: QLineEdit, button: QPushButton) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(field, 1)
        row.addWidget(button)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _snapshot_formulario(self) -> dict[str, str]:
        return {
            "paciente_id": str(self._paciente_id or ""),
            "medico_id": str(self._medico_id or ""),
            "sala_id": str(self._sala_id or ""),
            "inicio": self.ed_inicio.text().strip(),
            "fin": self.ed_fin.text().strip(),
            "motivo": self.ed_motivo.text().strip(),
            "observaciones": self.ed_obs.toPlainText().strip(),
        }

    def _validar_campos(self, valores: dict[str, str]) -> dict[str, str]:
        return validar_formulario_cita(valores, i18n=self._i18n)

    def _on_form_changed(self, *_: object) -> None:
        self._control_estado.actualizar_valores(self._snapshot_formulario())
        self._control_estado.limpiar_error_guardado()
        self._aplicar_estado()

    def _aplicar_estado(self) -> None:
        estado = self._control_estado.estado
        self.btn_ok.setEnabled(estado.listo_para_enviar and not self._submit_en_curso)
        self.btn_ok.setText(self._i18n.t("form.guardando") if estado.guardando else self._i18n.t("citas.form.crear"))
        self.lbl_error.setText(estado.error_guardado or "")
        for clave, label in self._labels_error.items():
            mensaje = estado.errores_validacion.get(clave, "")
            label.setText(mensaje)
            label.setVisible(bool(mensaje))

    def _select_paciente(self) -> None:
        selection = select_paciente(self, self._container.connection)
        if not selection:
            return
        self._paciente_id = selection.entity_id
        self.ed_paciente.setText(selection.display)
        self._on_form_changed()

    def _select_medico(self) -> None:
        selection = select_medico(self, self._container.connection)
        if not selection:
            return
        self._medico_id = selection.entity_id
        self.ed_medico.setText(selection.display)
        self._on_form_changed()

    def _select_sala(self) -> None:
        selection = select_sala(self, self._container.connection)
        if not selection:
            return
        self._sala_id = selection.entity_id
        self.ed_sala.setText(selection.display)
        self._on_form_changed()

    def _on_ok(self) -> None:
        if self._submit_en_curso:
            return
        estado = self._control_estado.actualizar_valores(self._snapshot_formulario())
        if not estado.valido:
            self._enfocar_primer_error(estado.errores_validacion)
            self._aplicar_estado()
            return
        self._submit_en_curso = True
        self._control_estado.marcar_guardando(True)
        self._aplicar_estado()
        self.accept()

    def _enfocar_primer_error(self, errores: dict[str, str]) -> None:
        widgets_por_campo = {
            "inicio": self.ed_inicio,
            "fin": self.ed_fin,
        }
        campo = primer_campo_con_error(errores, tuple(widgets_por_campo.keys()))
        if campo:
            widgets_por_campo[campo].setFocus()

    def reject(self) -> None:
        self._control_estado.actualizar_valores(self._snapshot_formulario(), validar=False)
        if self._control_estado.estado.cambios_sin_guardar:
            respuesta = QMessageBox.question(
                self,
                self._i18n.t("form.unsaved.title"),
                self._i18n.t("form.unsaved.message"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if respuesta != QMessageBox.Yes:
                return
        super().reject()

    def get_data(self) -> Optional[CitaFormData]:
        if self.result() != QDialog.Accepted:
            return None
        self._control_estado.marcar_guardado_exitoso()
        return CitaFormData(
            paciente_id=int(self._paciente_id or 0),
            medico_id=int(self._medico_id or 0),
            sala_id=int(self._sala_id or 0),
            inicio=self.ed_inicio.text().strip(),
            fin=self.ed_fin.text().strip(),
            motivo=(self.ed_motivo.text() or "").strip() or None,
            observaciones=(self.ed_obs.toPlainText() or "").strip() or None,
        )

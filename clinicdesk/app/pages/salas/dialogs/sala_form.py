from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QWidget,
)

from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Sala
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.label_utils import required_label


@dataclass(slots=True)
class SalaFormData:
    sala: Sala


class SalaFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sala")
        self._sala_id: Optional[int] = None

        self.txt_nombre = QLineEdit()
        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItems([t.value for t in TipoSala])
        self.txt_ubicacion = QLineEdit()
        self.chk_activa = QCheckBox("Activa")
        self.chk_activa.setChecked(True)

        form = QFormLayout()
        form.addRow(required_label("Nombre"), self.txt_nombre)
        form.addRow(required_label("Tipo"), self.cbo_tipo)
        form.addRow("Ubicación", self.txt_ubicacion)
        form.addRow("", self.chk_activa)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_sala(self, sala: Sala) -> None:
        self._sala_id = sala.id
        self.txt_nombre.setText(sala.nombre)
        self.cbo_tipo.setCurrentText(sala.tipo.value)
        self.txt_ubicacion.setText(sala.ubicacion or "")
        self.chk_activa.setChecked(sala.activa)

    def get_data(self) -> Optional[SalaFormData]:
        try:
            sala = Sala(
                id=self._sala_id,
                nombre=self.txt_nombre.text().strip(),
                tipo=TipoSala(self.cbo_tipo.currentText()),
                ubicacion=self.txt_ubicacion.text().strip() or None,
                activa=self.chk_activa.isChecked(),
            )
            sala.validar()
        except ValidationError as exc:
            present_error(self, exc)
            return None

        return SalaFormData(sala=sala)

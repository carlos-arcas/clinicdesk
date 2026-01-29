from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

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

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.infrastructure.sqlite.repos_turnos import Turno
from clinicdesk.app.ui.error_presenter import present_error


@dataclass(slots=True)
class BloqueFormData:
    fecha: str
    turno_id: int
    hora_inicio_override: Optional[str]
    hora_fin_override: Optional[str]
    observaciones: Optional[str]
    activo: bool


class BloqueFormDialog(QDialog):
    def __init__(self, turnos: List[Turno], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bloque de calendario")

        self.txt_fecha = QLineEdit()
        self.cbo_turno = QComboBox()
        self._turno_ids: List[int] = []
        for t in turnos:
            self.cbo_turno.addItem(f"{t.id} - {t.nombre} ({t.hora_inicio}-{t.hora_fin})")
            self._turno_ids.append(int(t.id))

        self.txt_inicio_override = QLineEdit()
        self.txt_fin_override = QLineEdit()
        self.txt_observaciones = QLineEdit()
        self.chk_activo = QCheckBox("Activo")
        self.chk_activo.setChecked(True)

        form = QFormLayout()
        form.addRow("Fecha (YYYY-MM-DD)", self.txt_fecha)
        form.addRow("Turno", self.cbo_turno)
        form.addRow("Hora inicio override (HH:MM)", self.txt_inicio_override)
        form.addRow("Hora fin override (HH:MM)", self.txt_fin_override)
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

    def get_data(self) -> Optional[BloqueFormData]:
        fecha = self.txt_fecha.text().strip()
        if not fecha:
            QMessageBox.warning(self, "Validación", "Fecha obligatoria.")
            return None

        if not self._turno_ids:
            QMessageBox.warning(self, "Validación", "No hay turnos disponibles.")
            return None

        try:
            turno_id = self._turno_ids[self.cbo_turno.currentIndex()]
        except IndexError:
            QMessageBox.warning(self, "Validación", "Turno inválido.")
            return None

        try:
            if turno_id <= 0:
                raise ValidationError("turno_id inválido.")
        except ValidationError as exc:
            present_error(self, exc)
            return None

        return BloqueFormData(
            fecha=fecha,
            turno_id=turno_id,
            hora_inicio_override=self.txt_inicio_override.text().strip() or None,
            hora_fin_override=self.txt_fin_override.text().strip() or None,
            observaciones=self.txt_observaciones.text().strip() or None,
            activo=self.chk_activo.isChecked(),
        )

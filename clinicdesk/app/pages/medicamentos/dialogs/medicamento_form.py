from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Medicamento


@dataclass(slots=True)
class MedicamentoFormData:
    medicamento: Medicamento


class MedicamentoFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Medicamento")
        self._medicamento_id: Optional[int] = None

        self.txt_nombre_comercial = QLineEdit()
        self.txt_nombre_compuesto = QLineEdit()
        self.spn_stock = QSpinBox()
        self.spn_stock.setRange(0, 1_000_000)
        self.chk_activo = QCheckBox("Activo")
        self.chk_activo.setChecked(True)

        form = QFormLayout()
        form.addRow("Nombre comercial", self.txt_nombre_comercial)
        form.addRow("Nombre compuesto", self.txt_nombre_compuesto)
        form.addRow("Stock", self.spn_stock)
        form.addRow("", self.chk_activo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def set_medicamento(self, medicamento: Medicamento) -> None:
        self._medicamento_id = medicamento.id
        self.txt_nombre_comercial.setText(medicamento.nombre_comercial)
        self.txt_nombre_compuesto.setText(medicamento.nombre_compuesto)
        self.spn_stock.setValue(medicamento.cantidad_en_almacen)
        self.chk_activo.setChecked(medicamento.activo)

    def get_data(self) -> Optional[MedicamentoFormData]:
        try:
            medicamento = Medicamento(
                id=self._medicamento_id,
                nombre_comercial=self.txt_nombre_comercial.text().strip(),
                nombre_compuesto=self.txt_nombre_compuesto.text().strip(),
                cantidad_en_almacen=self.spn_stock.value(),
                activo=self.chk_activo.isChecked(),
            )
            medicamento.validar()
        except ValidationError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return None

        return MedicamentoFormData(medicamento=medicamento)

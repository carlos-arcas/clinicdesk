from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.modelos import Material
from clinicdesk.app.ui.error_presenter import present_error
from clinicdesk.app.ui.label_utils import required_label


@dataclass(slots=True)
class MaterialFormData:
    material: Material


class MaterialFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Material")
        self._material_id: Optional[int] = None

        self.txt_nombre = QLineEdit()
        self.chk_fungible = QCheckBox("Fungible")
        self.chk_fungible.setChecked(True)
        self.spn_stock = QSpinBox()
        self.spn_stock.setRange(0, 1_000_000)
        self.chk_activo = QCheckBox("Activo")
        self.chk_activo.setChecked(True)

        form = QFormLayout()
        form.addRow(required_label("Nombre"), self.txt_nombre)
        form.addRow("", self.chk_fungible)
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

    def set_material(self, material: Material) -> None:
        self._material_id = material.id
        self.txt_nombre.setText(material.nombre)
        self.chk_fungible.setChecked(material.fungible)
        self.spn_stock.setValue(material.cantidad_en_almacen)
        self.chk_activo.setChecked(material.activo)

    def get_data(self) -> Optional[MaterialFormData]:
        try:
            material = Material(
                id=self._material_id,
                nombre=self.txt_nombre.text().strip(),
                fungible=self.chk_fungible.isChecked(),
                cantidad_en_almacen=self.spn_stock.value(),
                activo=self.chk_activo.isChecked(),
            )
            material.validar()
        except ValidationError as exc:
            present_error(self, exc)
            return None

        return MaterialFormData(material=material)

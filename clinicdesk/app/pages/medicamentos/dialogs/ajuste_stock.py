from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)

from clinicdesk.app.domain.exceptions import ValidationError


@dataclass(slots=True)
class AjusteStockData:
    tipo: str
    cantidad: int
    personal_id: int
    motivo: Optional[str]
    referencia: Optional[str]


class AjusteStockDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajustar stock")

        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItems(["ENTRADA", "SALIDA", "AJUSTE"])

        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1_000_000)

        self.txt_personal_id = QLineEdit()
        self.txt_motivo = QLineEdit()
        self.txt_referencia = QLineEdit()

        form = QFormLayout()
        form.addRow("Tipo", self.cbo_tipo)
        form.addRow("Cantidad", self.spn_cantidad)
        form.addRow("Personal ID", self.txt_personal_id)
        form.addRow("Motivo", self.txt_motivo)
        form.addRow("Referencia", self.txt_referencia)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def get_data(self) -> Optional[AjusteStockData]:
        try:
            personal_id = int(self.txt_personal_id.text().strip())
            if personal_id <= 0:
                raise ValidationError("personal_id inválido.")
        except (ValueError, ValidationError) as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return None

        return AjusteStockData(
            tipo=self.cbo_tipo.currentText(),
            cantidad=int(self.spn_cantidad.value()),
            personal_id=personal_id,
            motivo=self.txt_motivo.text().strip() or None,
            referencia=self.txt_referencia.text().strip() or None,
        )

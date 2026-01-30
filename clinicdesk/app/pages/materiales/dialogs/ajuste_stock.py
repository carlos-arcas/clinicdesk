from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.pages.shared.selector_dialog import select_personal
from clinicdesk.app.ui.error_presenter import present_error


@dataclass(slots=True)
class AjusteStockData:
    tipo: str
    cantidad: int
    personal_id: int
    motivo: Optional[str]


class AjusteStockDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, *, container: AppContainer) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajustar stock")

        self._container = container
        self._personal_id: Optional[int] = None

        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItems(["ENTRADA", "SALIDA", "AJUSTE"])

        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1_000_000)

        self.txt_personal_id = QLineEdit()
        self.txt_personal_id.setReadOnly(True)
        self.btn_personal = QPushButton("Buscar…")
        self.btn_personal.clicked.connect(self._select_personal)
        self.txt_motivo = QLineEdit()

        form = QFormLayout()
        form.addRow("Tipo", self.cbo_tipo)
        form.addRow("Cantidad", self.spn_cantidad)
        form.addRow("Personal", self._selector_row())
        form.addRow("Motivo", self.txt_motivo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def _selector_row(self) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(self.txt_personal_id, 1)
        row.addWidget(self.btn_personal)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _select_personal(self) -> None:
        selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._personal_id = selection.entity_id
        self.txt_personal_id.setText(selection.display)

    def get_data(self) -> Optional[AjusteStockData]:
        if not self._personal_id:
            present_error(self, ValidationError("Selecciona el personal que realiza el ajuste."))
            return None

        return AjusteStockData(
            tipo=self.cbo_tipo.currentText(),
            cantidad=int(self.spn_cantidad.value()),
            personal_id=int(self._personal_id or 0),
            motivo=self.txt_motivo.text().strip() or None,
        )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.shared.selector_dialog import select_personal


@dataclass(slots=True)
class AusenciaFormData:
    inicio: str
    fin: str
    tipo: str
    motivo: Optional[str]
    aprobado_por_personal_id: Optional[int]
    creado_en: str


class AusenciaFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, *, container: AppContainer) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ausencia")

        self._container = container
        self._aprobado_por_id: Optional[int] = None

        self.txt_inicio = QLineEdit()
        self.txt_fin = QLineEdit()
        self.txt_tipo = QLineEdit()
        self.txt_motivo = QLineEdit()
        self.txt_aprobado_por = QLineEdit()
        self.txt_aprobado_por.setReadOnly(True)
        self.btn_aprobado_por = QPushButton("Buscar…")
        self.btn_aprobado_por.clicked.connect(self._select_aprobador)
        self.btn_limpiar_aprobador = QPushButton("Limpiar")
        self.btn_limpiar_aprobador.clicked.connect(self._clear_aprobador)

        form = QFormLayout()
        form.addRow("Inicio (YYYY-MM-DD)", self.txt_inicio)
        form.addRow("Fin (YYYY-MM-DD)", self.txt_fin)
        form.addRow("Tipo", self.txt_tipo)
        form.addRow("Motivo", self.txt_motivo)
        form.addRow("Aprobado por (opcional)", self._build_aprobador_row())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def _build_aprobador_row(self) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(self.txt_aprobado_por, 1)
        row.addWidget(self.btn_aprobado_por)
        row.addWidget(self.btn_limpiar_aprobador)
        wrapper = QWidget()
        wrapper.setLayout(row)
        return wrapper

    def _select_aprobador(self) -> None:
        selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._aprobado_por_id = selection.entity_id
        self.txt_aprobado_por.setText(selection.display)

    def _clear_aprobador(self) -> None:
        self._aprobado_por_id = None
        self.txt_aprobado_por.clear()

    def get_data(self) -> Optional[AusenciaFormData]:
        inicio = self.txt_inicio.text().strip()
        fin = self.txt_fin.text().strip()
        tipo = self.txt_tipo.text().strip()
        if not inicio or not fin or not tipo:
            QMessageBox.warning(self, "Validación", "Inicio, fin y tipo son obligatorios.")
            return None

        return AusenciaFormData(
            inicio=inicio,
            fin=fin,
            tipo=tipo,
            motivo=self.txt_motivo.text().strip() or None,
            aprobado_por_personal_id=self._aprobado_por_id,
            creado_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from clinicdesk.app.domain.exceptions import ValidationError


@dataclass(slots=True)
class AusenciaFormData:
    inicio: str
    fin: str
    tipo: str
    motivo: Optional[str]
    aprobado_por_personal_id: Optional[int]
    creado_en: str


class AusenciaFormDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ausencia")

        self.txt_inicio = QLineEdit()
        self.txt_fin = QLineEdit()
        self.txt_tipo = QLineEdit()
        self.txt_motivo = QLineEdit()
        self.txt_aprobado_por = QLineEdit()

        form = QFormLayout()
        form.addRow("Inicio (YYYY-MM-DD)", self.txt_inicio)
        form.addRow("Fin (YYYY-MM-DD)", self.txt_fin)
        form.addRow("Tipo", self.txt_tipo)
        form.addRow("Motivo", self.txt_motivo)
        form.addRow("Aprobado por (personal id)", self.txt_aprobado_por)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow(form)
        layout.addRow(buttons)

    def get_data(self) -> Optional[AusenciaFormData]:
        inicio = self.txt_inicio.text().strip()
        fin = self.txt_fin.text().strip()
        tipo = self.txt_tipo.text().strip()
        if not inicio or not fin or not tipo:
            QMessageBox.warning(self, "Validación", "Inicio, fin y tipo son obligatorios.")
            return None

        aprobado_por_raw = self.txt_aprobado_por.text().strip()
        aprobado_por = None
        if aprobado_por_raw:
            try:
                aprobado_por = int(aprobado_por_raw)
                if aprobado_por <= 0:
                    raise ValidationError("aprobado_por_personal_id inválido")
            except (ValueError, ValidationError) as exc:
                QMessageBox.warning(self, "Validación", str(exc))
                return None

        return AusenciaFormData(
            inicio=inicio,
            fin=fin,
            tipo=tipo,
            motivo=self.txt_motivo.text().strip() or None,
            aprobado_por_personal_id=aprobado_por,
            creado_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

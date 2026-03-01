from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QPushButton, QVBoxLayout

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.atributos_cita import ATRIBUTOS_CITA, claves_visibles_por_defecto


class SelectorColumnasCitasDialog(QDialog):
    def __init__(self, i18n: I18nManager, visibles: list[str], parent=None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._checks: dict[str, QCheckBox] = {}
        self.setWindowTitle(self._i18n.t("citas.columnas.titulo"))

        layout = QVBoxLayout(self)
        for atributo in ATRIBUTOS_CITA:
            check = QCheckBox(self._i18n.t(atributo.clave_i18n), self)
            check.setChecked(atributo.clave in visibles)
            self._checks[atributo.clave] = check
            layout.addWidget(check)

        actions = QHBoxLayout()
        self.btn_reset = QPushButton(self._i18n.t("citas.columnas.restablecer"), self)
        self.btn_reset.clicked.connect(self._reset)
        actions.addWidget(self.btn_reset)
        actions.addStretch(1)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def columnas_seleccionadas(self) -> list[str]:
        columnas = [clave for clave, check in self._checks.items() if check.isChecked()]
        return columnas or claves_visibles_por_defecto()

    def _reset(self) -> None:
        columnas = set(claves_visibles_por_defecto())
        for clave, check in self._checks.items():
            check.setChecked(clave in columnas)

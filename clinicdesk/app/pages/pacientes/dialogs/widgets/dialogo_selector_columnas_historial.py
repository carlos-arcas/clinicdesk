from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from clinicdesk.app.application.historial_paciente.atributos import AtributoHistorial
from clinicdesk.app.i18n import I18nManager


class DialogoSelectorColumnasHistorial(QDialog):
    def __init__(
        self,
        i18n: I18nManager,
        contrato: tuple[AtributoHistorial, ...],
        seleccionadas: tuple[str, ...],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._contrato = contrato
        self._checks: dict[str, QCheckBox] = {}
        self._build_ui(seleccionadas)

    def _build_ui(self, seleccionadas: tuple[str, ...]) -> None:
        root = QVBoxLayout(self)
        for atributo in self._contrato:
            if atributo.clave.endswith("_id"):
                continue
            check = QCheckBox(self._i18n.t(atributo.i18n_key_cabecera), self)
            check.setChecked(atributo.clave in seleccionadas)
            self._checks[atributo.clave] = check
            root.addWidget(check)
        acciones = QHBoxLayout()
        self.btn_reset = QPushButton(self._i18n.t("historial.columnas.restablecer"), self)
        self.btn_reset.clicked.connect(self._restablecer)
        self.btn_cancelar = QPushButton(self._i18n.t("comun.cancelar"), self)
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar = QPushButton(self._i18n.t("comun.guardar"), self)
        self.btn_guardar.clicked.connect(self.accept)
        acciones.addWidget(self.btn_reset)
        acciones.addStretch(1)
        acciones.addWidget(self.btn_cancelar)
        acciones.addWidget(self.btn_guardar)
        root.addLayout(acciones)

    def columnas_seleccionadas(self) -> tuple[str, ...]:
        seleccion = tuple(clave for clave, check in self._checks.items() if check.isChecked())
        return seleccion

    def _restablecer(self) -> None:
        for atributo in self._contrato:
            check = self._checks.get(atributo.clave)
            if check is not None:
                check.setChecked(atributo.visible_por_defecto)

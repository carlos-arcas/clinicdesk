from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.citas import ATRIBUTOS_CITA, sanear_columnas_citas
from clinicdesk.app.i18n import I18nManager


class DialogoSelectorColumnasCitas(QDialog):
    def __init__(self, i18n: I18nManager, columnas_actuales: tuple[str, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._checks: dict[str, QCheckBox] = {}
        self._columnas_actuales, _ = sanear_columnas_citas(columnas_actuales)
        self._build_ui()
        self._retranslate()
        self._marcar_actuales()

    def columnas_seleccionadas(self) -> tuple[str, ...]:
        seleccion = [clave for clave, check in self._checks.items() if check.isChecked()]
        saneadas, _ = sanear_columnas_citas(tuple(seleccion))
        return saneadas

    def _build_ui(self) -> None:
        self.setModal(True)
        self.layout_principal = QVBoxLayout(self)
        self.lbl_info = QLabel(self)
        self.layout_principal.addWidget(self.lbl_info)
        for descriptor in ATRIBUTOS_CITA:
            if descriptor.clave == "cita_id":
                continue
            check = QCheckBox(self)
            self._checks[descriptor.clave] = check
            self.layout_principal.addWidget(check)
        barra = QHBoxLayout()
        self.btn_restablecer = QPushButton(self)
        barra.addWidget(self.btn_restablecer)
        barra.addStretch(1)
        self.layout_principal.addLayout(barra)
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        self.layout_principal.addWidget(botones)
        self.btn_restablecer.clicked.connect(self._restablecer)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._i18n.t("citas.lista.columnas.titulo"))
        self.lbl_info.setText(self._i18n.t("citas.lista.columnas.descripcion"))
        self.btn_restablecer.setText(self._i18n.t("citas.lista.columnas.restablecer"))
        for descriptor in ATRIBUTOS_CITA:
            check = self._checks.get(descriptor.clave)
            if check is not None:
                check.setText(self._i18n.t(descriptor.i18n_key_cabecera))

    def _marcar_actuales(self) -> None:
        for clave, check in self._checks.items():
            check.setChecked(clave in self._columnas_actuales)

    def _restablecer(self) -> None:
        saneadas, _ = sanear_columnas_citas(None)
        for clave, check in self._checks.items():
            check.setChecked(clave in saneadas)

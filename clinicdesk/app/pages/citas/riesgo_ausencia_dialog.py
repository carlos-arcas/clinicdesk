from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from clinicdesk.app.application.prediccion_ausencias.dtos import ExplicacionRiesgoAusenciaDTO
from clinicdesk.app.i18n import I18nManager


class RiesgoAusenciaDialog(QDialog):
    def __init__(self, i18n: I18nManager, explicacion: ExplicacionRiesgoAusenciaDTO, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._explicacion = explicacion
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(self._i18n.t("citas.riesgo_dialogo.titulo"))
        self.setMinimumWidth(460)
        root = QVBoxLayout(self)

        root.addWidget(QLabel(self._texto_nivel()))
        root.addWidget(QLabel(self._i18n.t("citas.riesgo_dialogo.seccion.por_que")))
        root.addWidget(self._crear_lista(self._motivos_texto()))

        root.addWidget(QLabel(self._i18n.t("citas.riesgo_dialogo.seccion.que_hacer")))
        root.addWidget(self._crear_lista(self._acciones_texto()))

        root.addWidget(QLabel(self._texto_actualizacion()))
        root.addLayout(self._crear_botonera())

    def _texto_nivel(self) -> str:
        nivel = self._i18n.t(f"citas.riesgo_dialogo.nivel.{self._explicacion.nivel.lower()}")
        return self._i18n.t("citas.riesgo_dialogo.riesgo_linea").format(nivel=nivel)

    def _motivos_texto(self) -> list[str]:
        items: list[str] = []
        for motivo in self._explicacion.motivos:
            texto = self._i18n.t(motivo.i18n_key)
            if motivo.detalle_suave_key:
                texto = f"{texto} {self._i18n.t(motivo.detalle_suave_key)}"
            items.append(texto)
        return items

    def _acciones_texto(self) -> list[str]:
        return [self._i18n.t(key) for key in self._explicacion.acciones_sugeridas]

    def _texto_actualizacion(self) -> str:
        if self._explicacion.metadata_simple.fecha_entrenamiento:
            return self._i18n.t("citas.riesgo_dialogo.ultima_actualizacion").format(
                fecha=self._explicacion.metadata_simple.fecha_entrenamiento
            )
        return self._i18n.t("citas.riesgo_dialogo.sin_actualizacion")

    def _crear_lista(self, items: list[str]) -> QListWidget:
        lista = QListWidget(self)
        for texto in items:
            lista.addItem(f"• {texto}")
        lista.setFocusPolicy(Qt.NoFocus)
        lista.setMaximumHeight(90)
        return lista

    def _crear_botonera(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.btn_ir_prediccion = QPushButton(self._i18n.t("citas.riesgo_dialogo.boton.ir_prediccion"), self)
        self.btn_cerrar = QPushButton(self._i18n.t("citas.riesgo_dialogo.boton.cerrar"), self)
        self.btn_cerrar.clicked.connect(self.reject)
        self.btn_ir_prediccion.setVisible(self._explicacion.metadata_simple.necesita_entrenar)
        layout.addWidget(self.btn_ir_prediccion)
        layout.addStretch(1)
        layout.addWidget(self.btn_cerrar)
        return layout

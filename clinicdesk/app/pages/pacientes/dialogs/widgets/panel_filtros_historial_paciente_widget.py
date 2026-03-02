from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from clinicdesk.app.application.historial_paciente.filtros import FiltrosHistorialPacienteDTO
from clinicdesk.app.i18n import I18nManager


class PanelFiltrosHistorialPacienteWidget(QWidget):
    aplicar_solicitado = Signal()
    limpiar_solicitado = Signal()

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        self.lbl_preset = QLabel(self)
        self.combo_preset = QComboBox(self)
        self.combo_preset.currentIndexChanged.connect(self._actualizar_visibilidad_personalizado)
        self.lbl_desde = QLabel(self)
        self.input_desde = QDateTimeEdit(self)
        self.input_desde.setCalendarPopup(True)
        self.lbl_hasta = QLabel(self)
        self.input_hasta = QDateTimeEdit(self)
        self.input_hasta.setCalendarPopup(True)
        self.lbl_buscar = QLabel(self)
        self.input_buscar = QLineEdit(self)
        self.lbl_estado = QLabel(self)
        self.combo_estado = QComboBox(self)
        self.btn_aplicar = QPushButton(self)
        self.btn_aplicar.clicked.connect(self.aplicar_solicitado.emit)
        self.btn_limpiar = QPushButton(self)
        self.btn_limpiar.clicked.connect(self.limpiar_solicitado.emit)
        for widget in (
            self.lbl_preset,
            self.combo_preset,
            self.lbl_desde,
            self.input_desde,
            self.lbl_hasta,
            self.input_hasta,
            self.lbl_buscar,
            self.input_buscar,
            self.lbl_estado,
            self.combo_estado,
            self.btn_aplicar,
            self.btn_limpiar,
        ):
            root.addWidget(widget)
        self.retranslate_ui()
        self._actualizar_visibilidad_personalizado()

    def retranslate_ui(self) -> None:
        self.lbl_preset.setText(self._i18n.t("historial.filtros.preset"))
        self.lbl_desde.setText(self._i18n.t("historial.filtros.desde"))
        self.lbl_hasta.setText(self._i18n.t("historial.filtros.hasta"))
        self.lbl_buscar.setText(self._i18n.t("historial.filtros.buscar"))
        self.lbl_estado.setText(self._i18n.t("historial.filtros.estado"))
        self.btn_aplicar.setText(self._i18n.t("historial.filtros.aplicar"))
        self.btn_limpiar.setText(self._i18n.t("historial.filtros.limpiar"))
        self.input_buscar.setPlaceholderText(self._i18n.t("historial.filtros.buscar.placeholder"))
        self.combo_preset.clear()
        self.combo_preset.addItem(self._i18n.t("historial.filtros.preset.30_dias"), "30_DIAS")
        self.combo_preset.addItem(self._i18n.t("historial.filtros.preset.12_meses"), "12_MESES")
        self.combo_preset.addItem(self._i18n.t("historial.filtros.preset.todo"), "TODO")
        self.combo_preset.addItem(self._i18n.t("historial.filtros.preset.personalizado"), "PERSONALIZADO")

    def set_estados(self, estados: tuple[str, ...]) -> None:
        actual = self.combo_estado.currentData()
        self.combo_estado.clear()
        self.combo_estado.addItem(self._i18n.t("historial.filtros.estado.todos"), None)
        for estado in estados:
            self.combo_estado.addItem(estado, estado)
        idx = self.combo_estado.findData(actual)
        self.combo_estado.setCurrentIndex(max(idx, 0))

    def construir_filtros(self, paciente_id: int) -> FiltrosHistorialPacienteDTO:
        preset = str(self.combo_preset.currentData())
        estado = self.combo_estado.currentData()
        return FiltrosHistorialPacienteDTO(
            paciente_id=paciente_id,
            rango_preset=preset,
            desde=self.input_desde.dateTime().toPython() if preset == "PERSONALIZADO" else None,
            hasta=self.input_hasta.dateTime().toPython() if preset == "PERSONALIZADO" else None,
            texto=self.input_buscar.text(),
            estados=(str(estado),) if estado else None,
        )

    def cargar_desde_dto(self, filtros: FiltrosHistorialPacienteDTO) -> None:
        idx = self.combo_preset.findData(filtros.rango_preset)
        self.combo_preset.setCurrentIndex(max(idx, 0))
        self.input_desde.setDateTime(filtros.desde or datetime.now())
        self.input_hasta.setDateTime(filtros.hasta or datetime.now())
        self.input_buscar.setText(filtros.texto or "")
        self._actualizar_visibilidad_personalizado()

    def limpiar(self) -> None:
        self.combo_preset.setCurrentIndex(0)
        self.input_buscar.clear()
        self.combo_estado.setCurrentIndex(0)
        self._actualizar_visibilidad_personalizado()

    def _actualizar_visibilidad_personalizado(self) -> None:
        visible = self.combo_preset.currentData() == "PERSONALIZADO"
        self.lbl_desde.setVisible(visible)
        self.input_desde.setVisible(visible)
        self.lbl_hasta.setVisible(visible)
        self.input_hasta.setVisible(visible)

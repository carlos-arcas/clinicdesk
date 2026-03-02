from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QComboBox, QDateEdit, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from clinicdesk.app.application.citas import FiltrosCitasDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.citas.estado_cita_presentacion import ESTADOS_FILTRO_CITAS


class PanelFiltrosCitasWidget(QWidget):
    filtros_aplicados = Signal(object)
    filtros_limpiados = Signal()

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._build_ui()
        self._bind_events()
        self._i18n.subscribe(self._retranslate)
        self._retranslate()
        self._on_preset_changed()

    def set_filtros(self, filtros: FiltrosCitasDTO) -> None:
        self._set_combo_data(self.cbo_preset, filtros.rango_preset or "HOY")
        if filtros.desde:
            self.desde_date.setDate(QDate(filtros.desde.year, filtros.desde.month, filtros.desde.day))
        if filtros.hasta:
            self.hasta_date.setDate(QDate(filtros.hasta.year, filtros.hasta.month, filtros.hasta.day))
        self.txt_busqueda.setText(filtros.texto_busqueda or "")
        self._set_combo_data(self.cbo_estado, filtros.estado_cita or "TODOS")
        self._on_preset_changed()

    def construir_dto(self) -> FiltrosCitasDTO:
        preset = str(self.cbo_preset.currentData() or "HOY")
        desde = self._dt_desde() if preset == "PERSONALIZADO" else None
        hasta = self._dt_hasta() if preset == "PERSONALIZADO" else None
        return FiltrosCitasDTO(
            rango_preset=preset,
            desde=desde,
            hasta=hasta,
            texto_busqueda=self.txt_busqueda.text().strip() or None,
            estado_cita=str(self.cbo_estado.currentData() or "TODOS"),
        )

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        self.lbl_preset = QLabel(self)
        self.cbo_preset = QComboBox(self)
        self.lbl_desde = QLabel(self)
        self.desde_date = QDateEdit(self)
        self.desde_date.setCalendarPopup(True)
        self.lbl_hasta = QLabel(self)
        self.hasta_date = QDateEdit(self)
        self.hasta_date.setCalendarPopup(True)
        self.txt_busqueda = QLineEdit(self)
        self.cbo_estado = QComboBox(self)
        self.btn_aplicar = QPushButton(self)
        self.btn_limpiar = QPushButton(self)

        layout.addWidget(self.lbl_preset)
        layout.addWidget(self.cbo_preset)
        layout.addWidget(self.lbl_desde)
        layout.addWidget(self.desde_date)
        layout.addWidget(self.lbl_hasta)
        layout.addWidget(self.hasta_date)
        layout.addWidget(self.txt_busqueda)
        layout.addWidget(self.cbo_estado)
        layout.addWidget(self.btn_aplicar)
        layout.addWidget(self.btn_limpiar)

    def _bind_events(self) -> None:
        self.cbo_preset.currentIndexChanged.connect(self._on_preset_changed)
        self.btn_aplicar.clicked.connect(self._emitir_aplicacion)
        self.btn_limpiar.clicked.connect(self._on_limpiar)

    def _retranslate(self) -> None:
        self.lbl_preset.setText(self._i18n.t("citas.filtros.preset"))
        self.lbl_desde.setText(self._i18n.t("citas.filtros.desde"))
        self.lbl_hasta.setText(self._i18n.t("citas.filtros.hasta"))
        self.txt_busqueda.setPlaceholderText(self._i18n.t("citas.filtros.buscar"))
        self.btn_aplicar.setText(self._i18n.t("citas.filtros.aplicar"))
        self.btn_limpiar.setText(self._i18n.t("citas.filtros.limpiar"))
        self._rebuild_presets()
        self._rebuild_estados()

    def _rebuild_presets(self) -> None:
        seleccionado = str(self.cbo_preset.currentData() or "HOY")
        self.cbo_preset.blockSignals(True)
        self.cbo_preset.clear()
        self.cbo_preset.addItem(self._i18n.t("citas.filtros.preset.hoy"), "HOY")
        self.cbo_preset.addItem(self._i18n.t("citas.filtros.preset.semana"), "SEMANA")
        self.cbo_preset.addItem(self._i18n.t("citas.filtros.preset.mes"), "MES")
        self.cbo_preset.addItem(self._i18n.t("citas.filtros.preset.personalizado"), "PERSONALIZADO")
        self._set_combo_data(self.cbo_preset, seleccionado)
        self.cbo_preset.blockSignals(False)

    def _rebuild_estados(self) -> None:
        seleccionado = str(self.cbo_estado.currentData() or "TODOS")
        self.cbo_estado.clear()
        for etiqueta, valor in ESTADOS_FILTRO_CITAS:
            self.cbo_estado.addItem(etiqueta, valor)
        self._set_combo_data(self.cbo_estado, seleccionado)

    def _set_combo_data(self, combo: QComboBox, valor: str) -> None:
        idx = combo.findData(valor)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    def enfocar_campo(self, campo: str | None) -> None:
        objetivos = {
            "desde": self.desde_date,
            "hasta": self.hasta_date,
            "texto_busqueda": self.txt_busqueda,
            "estado_cita": self.cbo_estado,
        }
        widget = objetivos.get(campo)
        if widget is not None:
            widget.setFocus()

    def restablecer_semana(self) -> None:
        self._set_combo_data(self.cbo_preset, "SEMANA")
        self.txt_busqueda.clear()
        self._set_combo_data(self.cbo_estado, "TODOS")
        self._on_preset_changed()

    def _on_preset_changed(self) -> None:
        visible = str(self.cbo_preset.currentData() or "") == "PERSONALIZADO"
        self.lbl_desde.setVisible(visible)
        self.desde_date.setVisible(visible)
        self.lbl_hasta.setVisible(visible)
        self.hasta_date.setVisible(visible)

    def _emitir_aplicacion(self) -> None:
        self.filtros_aplicados.emit(self.construir_dto())

    def _on_limpiar(self) -> None:
        self._set_combo_data(self.cbo_preset, "HOY")
        hoy = QDate.currentDate()
        self.desde_date.setDate(hoy)
        self.hasta_date.setDate(hoy)
        self.txt_busqueda.clear()
        self._set_combo_data(self.cbo_estado, "TODOS")
        self._on_preset_changed()
        self.filtros_limpiados.emit()
        self._emitir_aplicacion()

    def _dt_desde(self) -> datetime:
        valor = self.desde_date.date().toPython()
        return datetime(valor.year, valor.month, valor.day, 0, 0, 0)

    def _dt_hasta(self) -> datetime:
        valor = self.hasta_date.date().toPython()
        return datetime(valor.year, valor.month, valor.day, 23, 59, 59)

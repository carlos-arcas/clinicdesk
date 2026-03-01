from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QDateEdit, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QWidget

from clinicdesk.app.i18n import I18nManager

from clinicdesk.app.pages.citas.filtros_citas_estado import FiltrosCitasEstado


class PanelFiltrosCitasWidget(QWidget):
    filtros_aplicar = Signal()
    filtros_limpiar = Signal()

    def __init__(self, i18n: I18nManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._i18n = i18n
        self._estado_items: list[tuple[str, str]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        self.txt_busqueda = QLineEdit(self)
        self.cbo_estado = QComboBox(self)
        self.desde_date = QDateEdit(self)
        self.hasta_date = QDateEdit(self)
        self.btn_hoy = QPushButton(self)
        self.btn_semana = QPushButton(self)
        self.btn_mes = QPushButton(self)
        self.btn_aplicar = QPushButton(self)
        self.btn_limpiar = QPushButton(self)

        for control in (self.desde_date, self.hasta_date):
            control.setCalendarPopup(True)

        self.btn_hoy.clicked.connect(self.set_hoy)
        self.btn_semana.clicked.connect(self._set_semana)
        self.btn_mes.clicked.connect(self._set_mes)
        self.btn_aplicar.clicked.connect(self.filtros_aplicar.emit)
        self.btn_limpiar.clicked.connect(self._on_limpiar)

        layout.addWidget(QLabel(self._i18n.t("citas.filtros.desde"), self))
        layout.addWidget(self.desde_date)
        layout.addWidget(QLabel(self._i18n.t("citas.filtros.hasta"), self))
        layout.addWidget(self.hasta_date)
        layout.addWidget(self.btn_hoy)
        layout.addWidget(self.btn_semana)
        layout.addWidget(self.btn_mes)
        layout.addWidget(self.txt_busqueda)
        layout.addWidget(self.cbo_estado)
        layout.addWidget(self.btn_aplicar)
        layout.addWidget(self.btn_limpiar)
        self._retraducir()

    def _retraducir(self) -> None:
        self.txt_busqueda.setPlaceholderText(self._i18n.t("citas.filtros.buscar"))
        self.btn_hoy.setText(self._i18n.t("citas.filtros.hoy"))
        self.btn_semana.setText(self._i18n.t("citas.filtros.semana"))
        self.btn_mes.setText(self._i18n.t("citas.filtros.mes"))
        self.btn_aplicar.setText(self._i18n.t("citas.filtros.aplicar"))
        self.btn_limpiar.setText(self._i18n.t("citas.filtros.limpiar"))

    def set_estado_items(self, items: list[tuple[str, str]], default_value: str) -> None:
        self._estado_items = items
        self.cbo_estado.clear()
        for etiqueta, valor in items:
            self.cbo_estado.addItem(etiqueta, valor)
        self._set_estado(default_value)

    def _set_estado(self, valor: str) -> None:
        idx = self.cbo_estado.findData(valor)
        self.cbo_estado.setCurrentIndex(idx if idx >= 0 else 0)

    def estado_actual(self) -> FiltrosCitasEstado:
        return FiltrosCitasEstado(
            desde=self.desde_date.date().toString("yyyy-MM-dd"),
            hasta=self.hasta_date.date().toString("yyyy-MM-dd"),
            texto=self.txt_busqueda.text().strip(),
            estado=self.cbo_estado.currentData() or "TODOS",
        )

    def aplicar_estado(self, estado: FiltrosCitasEstado) -> None:
        self.desde_date.setDate(QDate.fromString(estado.desde, "yyyy-MM-dd"))
        self.hasta_date.setDate(QDate.fromString(estado.hasta, "yyyy-MM-dd"))
        self.txt_busqueda.setText(estado.texto)
        self._set_estado(estado.estado)

    def set_hoy(self) -> None:
        today = QDate.currentDate()
        self.desde_date.setDate(today)
        self.hasta_date.setDate(today)

    def _set_semana(self) -> None:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        self.desde_date.setDate(QDate(start.year, start.month, start.day))
        self.hasta_date.setDate(QDate(end.year, end.month, end.day))

    def _set_mes(self) -> None:
        today = date.today()
        start = today.replace(day=1)
        end = today.replace(day=31) if today.month == 12 else today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        self.desde_date.setDate(QDate(start.year, start.month, start.day))
        self.hasta_date.setDate(QDate(end.year, end.month, end.day))

    def _on_limpiar(self) -> None:
        self.txt_busqueda.clear()
        self._set_estado("TODOS")
        self.set_hoy()
        self.filtros_limpiar.emit()

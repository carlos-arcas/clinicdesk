from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FiltroListadoWidget(QWidget):
    filtros_cambiados = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)

        layout = QHBoxLayout(self)
        self.txt_busqueda = QLineEdit(self)
        self.txt_busqueda.setPlaceholderText(self.tr("Buscar..."))
        self.cbo_estado = QComboBox(self)
        self.cbo_estado.addItems(["Activos", "Inactivos", "Todos"])
        self.btn_limpiar = QPushButton(self.tr("Limpiar"), self)
        self.lbl_contador = QLabel(self.tr("Mostrando 0 de 0"), self)

        layout.addWidget(self.txt_busqueda)
        layout.addWidget(self.cbo_estado)
        layout.addWidget(self.btn_limpiar)
        layout.addStretch(1)
        layout.addWidget(self.lbl_contador)

        self._debounce.timeout.connect(self.filtros_cambiados.emit)
        self.txt_busqueda.textChanged.connect(self._on_filter_change)
        self.cbo_estado.currentIndexChanged.connect(self._on_filter_change)
        self.btn_limpiar.clicked.connect(self._on_limpiar)

    def texto(self) -> str:
        return self.txt_busqueda.text().strip()

    def activo(self) -> bool | None:
        value = self.cbo_estado.currentText()
        if value == "Activos":
            return True
        if value == "Inactivos":
            return False
        return None

    def estado(self) -> str:
        return self.cbo_estado.currentData() or self.cbo_estado.currentText()

    def set_estado_items(self, items: list[tuple[str, str]], default_value: str) -> None:
        self.cbo_estado.blockSignals(True)
        self.cbo_estado.clear()
        for etiqueta, valor in items:
            self.cbo_estado.addItem(etiqueta, valor)
        index = self.cbo_estado.findData(default_value)
        self.cbo_estado.setCurrentIndex(index if index >= 0 else 0)
        self.cbo_estado.blockSignals(False)

    def set_contador(self, mostrados: int, totales: int) -> None:
        self.lbl_contador.setText(self.tr("Mostrando {mostrados} de {totales}").format(mostrados=mostrados, totales=totales))

    def limpiar(self) -> None:
        self.txt_busqueda.clear()
        idx = self.cbo_estado.findData("TODOS")
        if idx < 0:
            idx = self.cbo_estado.findText("Todos")
        self.cbo_estado.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_filter_change(self) -> None:
        self._debounce.start()

    def _on_limpiar(self) -> None:
        self.limpiar()
        self.filtros_cambiados.emit()

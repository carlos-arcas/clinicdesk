from __future__ import annotations

from typing import Callable, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)

from clinicdesk.app.application.csv.csv_service import CsvService
from clinicdesk.app.controllers.csv_controller import CsvController
from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.pages_registry import get_pages



class MainWindow(QMainWindow):
    def __init__(self, container: AppContainer) -> None:
        super().__init__()
        self.container = container
        self._csv_controller = CsvController(
            self,
            CsvService(container),
            on_import_complete=self._on_csv_imported,
        )

        self.setWindowTitle("ClinicDesk")
        self.resize(1200, 800)

        root = QWidget()
        self.setCentralWidget(root)

        self._build_menu()

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setSelectionMode(QListWidget.SingleSelection)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        self._page_index_by_key: Dict[str, int] = {}
        self._factory_by_key: Dict[str, Callable[[], QWidget]] = {}

        # Páginas se crean bajo demanda (lazy) gracias a factory/lambda.
        for p in get_pages(container):
            self._factory_by_key[p.key] = p.factory
            item = QListWidgetItem(p.title)
            item.setData(Qt.UserRole, p.key)  # Qt.UserRole: almacenamiento de datos asociado al item.
            self.sidebar.addItem(item)

        self.sidebar.currentRowChanged.connect(self._on_sidebar_changed)

        self.navigate("home")

    def open_csv_dialog(self) -> None:
        self._csv_controller.open_dialog()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        menu_archivo = menu_bar.addMenu("Archivo")

        action_csv = QAction("Importar/Exportar CSV…", self)
        action_csv.triggered.connect(self._csv_controller.open_dialog)

        action_exit = QAction("Salir", self)
        action_exit.triggered.connect(self.close)

        menu_archivo.addAction(action_csv)
        menu_archivo.addSeparator()
        menu_archivo.addAction(action_exit)

    def _on_csv_imported(self, entity: str) -> None:
        key_by_entity = {
            "Pacientes": "pacientes",
            "Médicos": "medicos",
            "Personal": "personal",
            "Medicamentos": "medicamentos",
            "Materiales": "materiales",
            "Salas": "salas",
        }
        key = key_by_entity.get(entity)
        if not key:
            return
        index = self._page_index_by_key.get(key)
        if index is None:
            return
        widget = self.stack.widget(index)
        if widget is not None and hasattr(widget, "on_show"):
            widget.on_show()

    def _ensure_page_created(self, key: str) -> Optional[int]:
        if key in self._page_index_by_key:
            return self._page_index_by_key[key]

        factory = self._factory_by_key.get(key)
        if factory is None:
            return None

        widget = factory()  # aquí se ejecuta el lambda -> se crea la página
        index = self.stack.addWidget(widget)
        self._page_index_by_key[key] = index
        return index

    def _call_on_hide_current(self) -> None:
        w = self.stack.currentWidget()
        if w is not None and hasattr(w, "on_hide"):
            w.on_hide()  # hook opcional

    def _call_on_show_index(self, index: int) -> None:
        w = self.stack.widget(index)
        if w is not None and hasattr(w, "on_show"):
            w.on_show()  # hook opcional

    def navigate(self, key: str) -> None:
        self.sidebar.blockSignals(True)
        try:
            self._call_on_hide_current()

            index = self._ensure_page_created(key)
            if index is None:
                return

            self.stack.setCurrentIndex(index)
            self._call_on_show_index(index)

            for row in range(self.sidebar.count()):
                it = self.sidebar.item(row)
                if it.data(Qt.UserRole) == key:
                    self.sidebar.setCurrentRow(row)
                    break
        finally:
            self.sidebar.blockSignals(False)

    def _on_sidebar_changed(self, row: int) -> None:
        if row < 0:
            return

        self._call_on_hide_current()

        item = self.sidebar.item(row)
        key = item.data(Qt.UserRole)

        index = self._ensure_page_created(key)
        if index is None:
            return

        self.stack.setCurrentIndex(index)
        self._call_on_show_index(index)

    def closeEvent(self, event):
        """Evento Qt que se dispara al cerrar la ventana. Cerramos la BD."""
        self.container.close()
        event.accept()

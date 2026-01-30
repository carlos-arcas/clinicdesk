from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.queries.medicos_queries import MedicosQueries
from clinicdesk.app.queries.medicamentos_queries import MedicamentosQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries
from clinicdesk.app.queries.personal_queries import PersonalQueries
from clinicdesk.app.queries.salas_queries import SalasQueries


@dataclass(slots=True)
class SelectorResult:
    entity_id: int
    display: str


FetchRows = Callable[[Optional[str]], Iterable[tuple[int, str, str, str]]]


class SelectorDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        *,
        title: str,
        headers: list[str],
        fetch_rows: FetchRows,
        placeholder: str = "Buscar…",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(680)

        self._fetch_rows = fetch_rows
        self._selection: Optional[SelectorResult] = None

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(placeholder)
        self.btn_search = QPushButton("Buscar")

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filtro"))
        search_row.addWidget(self.txt_search)
        search_row.addWidget(self.btn_search)

        self.table = QTableWidget(0, len(headers) + 1)
        self.table.setHorizontalHeaderLabels(["ID", *headers])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Seleccionar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self.table)
        layout.addWidget(buttons)

        self.btn_search.clicked.connect(self._refresh)
        self.txt_search.returnPressed.connect(self._refresh)
        self.table.itemDoubleClicked.connect(lambda _: self._accept_selection())
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)

        self._refresh()

    def _refresh(self) -> None:
        rows = list(self._fetch_rows(self.txt_search.text().strip() or None))
        self.table.setRowCount(0)
        for data in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(data[0])))
            for col_idx, value in enumerate(data[1:], start=1):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def _accept_selection(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        id_item = self.table.item(row, 0)
        if not id_item:
            return
        try:
            entity_id = int(id_item.text())
        except ValueError:
            return

        display_parts = []
        for col in range(1, self.table.columnCount()):
            item = self.table.item(row, col)
            if item and item.text():
                display_parts.append(item.text())
        display = " · ".join(display_parts) if display_parts else str(entity_id)
        self._selection = SelectorResult(entity_id=entity_id, display=display)
        self.accept()

    def get_selection(self) -> Optional[SelectorResult]:
        if self.result() != QDialog.Accepted:
            return None
        return self._selection


def select_paciente(parent: QWidget, connection, *, activo: bool = True) -> Optional[SelectorResult]:
    queries = PacientesQueries(connection)

    def fetch_rows(texto: Optional[str]) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo)
        for row in rows:
            yield (row.id, row.documento, row.nombre_completo, row.telefono)

    dialog = SelectorDialog(
        parent,
        title="Seleccionar paciente",
        headers=["Documento", "Nombre", "Teléfono"],
        fetch_rows=fetch_rows,
        placeholder="Documento, nombre o teléfono…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()


def select_medico(parent: QWidget, connection, *, activo: bool = True) -> Optional[SelectorResult]:
    queries = MedicosQueries(connection)

    def fetch_rows(texto: Optional[str]) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo)
        for row in rows:
            yield (row.id, row.documento, row.nombre_completo, row.especialidad)

    dialog = SelectorDialog(
        parent,
        title="Seleccionar médico",
        headers=["Documento", "Nombre", "Especialidad"],
        fetch_rows=fetch_rows,
        placeholder="Documento, nombre, teléfono o especialidad…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()


def select_personal(parent: QWidget, connection, *, activo: bool = True) -> Optional[SelectorResult]:
    queries = PersonalQueries(connection)

    def fetch_rows(texto: Optional[str]) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo)
        for row in rows:
            yield (row.id, row.documento, row.nombre_completo, row.puesto)

    dialog = SelectorDialog(
        parent,
        title="Seleccionar personal",
        headers=["Documento", "Nombre", "Puesto"],
        fetch_rows=fetch_rows,
        placeholder="Documento, nombre, teléfono o puesto…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()


def select_sala(parent: QWidget, connection, *, activa: bool = True) -> Optional[SelectorResult]:
    queries = SalasQueries(connection)

    def fetch_rows(texto: Optional[str]) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activa=activa)
        for row in rows:
            ubicacion = row.ubicacion or ""
            yield (row.id, row.nombre, row.tipo, ubicacion)

    dialog = SelectorDialog(
        parent,
        title="Seleccionar sala",
        headers=["Nombre", "Tipo", "Ubicación"],
        fetch_rows=fetch_rows,
        placeholder="Nombre o ubicación…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()


def select_medicamento(parent: QWidget, connection, *, activo: bool = True) -> Optional[SelectorResult]:
    queries = MedicamentosQueries(connection)

    def fetch_rows(texto: Optional[str]) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo)
        for row in rows:
            yield (row.id, row.nombre_comercial, row.nombre_compuesto, str(row.stock))

    dialog = SelectorDialog(
        parent,
        title="Seleccionar medicamento",
        headers=["Nombre comercial", "Compuesto", "Stock"],
        fetch_rows=fetch_rows,
        placeholder="Nombre comercial o compuesto…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()

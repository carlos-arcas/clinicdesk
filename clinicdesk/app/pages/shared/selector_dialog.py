from __future__ import annotations

from dataclasses import dataclass
import logging
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

from clinicdesk.app.common.search_utils import normalize_search_text
from clinicdesk.app.queries.medicos_queries import MedicosQueries
from clinicdesk.app.queries.medicamentos_queries import MedicamentosQueries
from clinicdesk.app.queries.pacientes_queries import PacientesQueries
from clinicdesk.app.queries.personal_queries import PersonalQueries
from clinicdesk.app.queries.salas_queries import SalasQueries


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SelectorResult:
    entity_id: int
    display: str


FetchRows = Callable[[Optional[str], int, int], Iterable[tuple[int, str, str, str]]]


class EntitySelectorDialog(QDialog):
    _PAGE_SIZE = 50

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
        self._page = 0

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

        self.lbl_page = QLabel("")
        self.btn_prev = QPushButton("Anterior")
        self.btn_next = QPushButton("Siguiente")
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)

        pagination = QHBoxLayout()
        pagination.addWidget(self.btn_prev)
        pagination.addWidget(self.btn_next)
        pagination.addWidget(self.lbl_page)
        pagination.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Seleccionar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self.table)
        layout.addLayout(pagination)
        layout.addWidget(buttons)

        self.btn_search.clicked.connect(self._on_search)
        self.txt_search.returnPressed.connect(self._on_search)
        self.btn_prev.clicked.connect(self._go_prev)
        self.btn_next.clicked.connect(self._go_next)
        self.table.itemDoubleClicked.connect(lambda _: self._accept_selection())
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)

        self._refresh()

    def _on_search(self) -> None:
        self._page = 0
        self._refresh()

    def _go_prev(self) -> None:
        if self._page <= 0:
            return
        self._page -= 1
        self._refresh()

    def _go_next(self) -> None:
        self._page += 1
        self._refresh()

    def _refresh(self) -> None:
        texto = normalize_search_text(self.txt_search.text())
        if not texto:
            logger.info("EntitySelectorDialog: búsqueda vacía, sin consulta.")
            self.table.setRowCount(0)
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.lbl_page.setText("")
            return

        offset = self._page * self._PAGE_SIZE
        rows = list(self._fetch_rows(texto, offset, self._PAGE_SIZE + 1))
        has_next = len(rows) > self._PAGE_SIZE
        page_rows = rows[: self._PAGE_SIZE]

        if self._page > 0 and not page_rows:
            self._page -= 1
            self._refresh()
            return

        self.table.setRowCount(0)
        for data in page_rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(data[0])))
            for col_idx, value in enumerate(data[1:], start=1):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        has_prev = self._page > 0
        self.btn_prev.setEnabled(has_prev)
        self.btn_next.setEnabled(has_next)

        if has_prev or has_next:
            self.lbl_page.setText(f"Página {self._page + 1}")
        else:
            self.lbl_page.setText(f"{len(page_rows)} resultados")

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

    def fetch_rows(texto: Optional[str], offset: int, limit: int) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo, limit=offset + limit)
        for row in rows[offset: offset + limit]:
            yield (row.id, row.documento, row.nombre_completo, row.telefono)

    dialog = EntitySelectorDialog(
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

    def fetch_rows(texto: Optional[str], offset: int, limit: int) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo, limit=limit, offset=offset)
        for row in rows:
            yield (row.id, row.documento, row.nombre_completo, row.especialidad)

    dialog = EntitySelectorDialog(
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

    def fetch_rows(texto: Optional[str], offset: int, limit: int) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo, limit=limit, offset=offset)
        for row in rows:
            yield (row.id, row.documento, row.nombre_completo, row.puesto)

    dialog = EntitySelectorDialog(
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

    def fetch_rows(texto: Optional[str], offset: int, limit: int) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activa=activa, limit=offset + limit)
        for row in rows[offset: offset + limit]:
            ubicacion = row.ubicacion or ""
            yield (row.id, row.nombre, row.tipo, ubicacion)

    dialog = EntitySelectorDialog(
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

    def fetch_rows(texto: Optional[str], offset: int, limit: int) -> Iterable[tuple[int, str, str, str]]:
        rows = queries.search(texto=texto, activo=activo, limit=offset + limit)
        for row in rows[offset: offset + limit]:
            yield (row.id, row.nombre_comercial, row.nombre_compuesto, str(row.stock))

    dialog = EntitySelectorDialog(
        parent,
        title="Seleccionar medicamento",
        headers=["Nombre comercial", "Compuesto", "Stock"],
        fetch_rows=fetch_rows,
        placeholder="Nombre comercial o compuesto…",
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    return dialog.get_selection()

from __future__ import annotations

from typing import Optional

import logging

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDialog,
)

from clinicdesk.app.container import AppContainer
from clinicdesk.app.pages.ausencias.dialogs.ausencia_form import AusenciaFormDialog
from clinicdesk.app.pages.shared.selector_dialog import select_medico, select_personal
from clinicdesk.app.queries.ausencias_queries import AusenciasQueries, AusenciaRow
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_medico import AusenciaMedico
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_personal import AusenciaPersonal
from clinicdesk.app.pages.shared.screen_data_log import log_screen_data_loaded


class PageAusencias(QWidget):
    def __init__(self, container: AppContainer, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._container = container
        self._queries = AusenciasQueries(container.connection)
        self._persona_id: Optional[int] = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.cbo_tipo = QComboBox()
        self.cbo_tipo.addItems(["Médico", "Personal"])
        self.txt_persona = QLineEdit()
        self.txt_persona.setReadOnly(True)
        self.btn_persona = QPushButton("Buscar…")
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate().addMonths(1))
        self.btn_cargar = QPushButton("Cargar")

        filters.addWidget(QLabel("Tipo"))
        filters.addWidget(self.cbo_tipo)
        filters.addWidget(QLabel("Persona"))
        filters.addWidget(self.txt_persona)
        filters.addWidget(self.btn_persona)
        filters.addWidget(QLabel("Desde"))
        filters.addWidget(self.date_desde)
        filters.addWidget(QLabel("Hasta"))
        filters.addWidget(self.date_hasta)
        filters.addWidget(self.btn_cargar)

        actions = QHBoxLayout()
        self.btn_nueva = QPushButton("Nueva ausencia")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setEnabled(False)
        actions.addWidget(self.btn_nueva)
        actions.addWidget(self.btn_eliminar)
        actions.addStretch(1)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Inicio", "Fin", "Tipo", "Motivo", "Aprobado por", "Creado en"]
        )
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        root.addLayout(filters)
        root.addLayout(actions)
        root.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.cbo_tipo.currentTextChanged.connect(self._reset_persona)
        self.btn_persona.clicked.connect(self._select_persona)
        self.btn_cargar.clicked.connect(self._refresh)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.btn_nueva.clicked.connect(self._on_nueva)
        self.btn_eliminar.clicked.connect(self._on_eliminar)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        persona_id = self._persona_id
        if persona_id is None:
            self.table.setRowCount(0)
            log_screen_data_loaded(self._container.connection, "ausencias", 0)
            return

        desde = self.date_desde.date().toString("yyyy-MM-dd")
        hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        if self.cbo_tipo.currentText() == "Médico":
            rows = self._queries.list_medico(persona_id, desde=desde, hasta=hasta)
        else:
            rows = self._queries.list_personal(persona_id, desde=desde, hasta=hasta)

        self._render(rows)
        log_screen_data_loaded(self._container.connection, "ausencias", len(rows))

    def _render(self, rows: list[AusenciaRow]) -> None:
        self.table.setRowCount(0)
        for a in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(a.id)))
            self.table.setItem(row, 1, QTableWidgetItem(a.inicio))
            self.table.setItem(row, 2, QTableWidgetItem(a.fin))
            self.table.setItem(row, 3, QTableWidgetItem(a.tipo))
            self.table.setItem(row, 4, QTableWidgetItem(a.motivo))
            self.table.setItem(row, 5, QTableWidgetItem(a.aprobado_por))
            self.table.setItem(row, 6, QTableWidgetItem(a.creado_en))

    def _on_selection_changed(self) -> None:
        self.btn_eliminar.setEnabled(self._selected_id() is not None)

    def _on_nueva(self) -> None:
        persona_id = self._persona_id
        if persona_id is None:
            QMessageBox.warning(self, "Ausencias", "Selecciona una persona.")
            return

        dialog = AusenciaFormDialog(self, container=self._container)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return

        if self.cbo_tipo.currentText() == "Médico":
            ausencia = AusenciaMedico(
                medico_id=persona_id,
                inicio=data.inicio,
                fin=data.fin,
                tipo=data.tipo,
                motivo=data.motivo,
                aprobado_por_personal_id=data.aprobado_por_personal_id,
                creado_en=data.creado_en,
            )
            self._container.ausencias_medico_repo.create(ausencia)
        else:
            ausencia = AusenciaPersonal(
                personal_id=persona_id,
                inicio=data.inicio,
                fin=data.fin,
                tipo=data.tipo,
                motivo=data.motivo,
                aprobado_por_personal_id=data.aprobado_por_personal_id,
                creado_en=data.creado_en,
            )
            self._container.ausencias_personal_repo.create(ausencia)

        self._refresh()

    def _on_eliminar(self) -> None:
        ausencia_id = self._selected_id()
        if not ausencia_id:
            return
        if QMessageBox.question(self, "Ausencias", "¿Eliminar ausencia?") != QMessageBox.Yes:
            return
        if self.cbo_tipo.currentText() == "Médico":
            self._container.ausencias_medico_repo.delete(ausencia_id)
        else:
            self._container.ausencias_personal_repo.delete(ausencia_id)
        self._refresh()

    def _selected_id(self) -> Optional[int]:
        items = self.table.selectedItems()
        if not items:
            return None
        try:
            return int(items[0].text())
        except ValueError:
            return None

    def _select_persona(self) -> None:
        if self.cbo_tipo.currentText() == "Médico":
            selection = select_medico(self, self._container.connection)
        else:
            selection = select_personal(self, self._container.connection)
        if not selection:
            return
        self._persona_id = selection.entity_id
        self.txt_persona.setText(selection.display)
        self._refresh()

    def _reset_persona(self) -> None:
        self._persona_id = None
        self.txt_persona.clear()
        self.table.setRowCount(0)

    def _open_context_menu(self, pos) -> None:
        row = self.table.rowAt(pos.y())
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        menu = QMenu(self)
        action_new = menu.addAction("Nueva ausencia")
        action_delete = menu.addAction("Eliminar")
        action_delete.setEnabled(self._selected_id() is not None)
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == action_new:
            self._on_nueva()
        elif action == action_delete:
            self._on_eliminar()


if __name__ == "__main__":
    logging.getLogger(__name__).info(
        "Este módulo no se ejecuta directamente. Usa: python -m clinicdesk"
    )
    raise SystemExit(2)

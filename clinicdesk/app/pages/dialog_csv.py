# app/ui/dialog_csv.py
"""
Diálogo PySide6 para Import/Export CSV.

Incluye:
- selector de entidad
- botones Importar / Exportar
- resumen de resultado
- tabla de errores por fila
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from clinicdesk.app.application.csv.csv_service import CsvImportResult
from clinicdesk.app.application.csv.csv_io import CsvRowError


class CsvDialog(QDialog):
    export_requested = Signal(str)  # entity
    import_requested = Signal(str)  # entity

    def __init__(self, parent: Optional[QWidget] = None, *, entities: List[str]) -> None:
        super().__init__(parent)
        self.setWindowTitle("Importar / Exportar CSV")
        self.setMinimumWidth(820)

        self._entities = entities

        # --- UI ---
        self.cbo_entity = QComboBox()
        self.cbo_entity.addItems(self._entities)

        self.btn_export = QPushButton("Exportar…")
        self.btn_import = QPushButton("Importar…")
        self.btn_close = QPushButton("Cerrar")

        self.lbl_path = QLabel("Ruta: —")
        self.lbl_summary = QLabel("Resumen: —")

        self.tbl_errors = QTableWidget(0, 4)
        self.tbl_errors.setHorizontalHeaderLabels(["Fila", "Error", "Campo(s)", "Valor(es)"])
        self.tbl_errors.setWordWrap(True)
        self.tbl_errors.horizontalHeader().setStretchLastSection(True)

        top = QHBoxLayout()
        top.addWidget(QLabel("Entidad:"))
        top.addWidget(self.cbo_entity)
        top.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        top.addWidget(self.btn_import)
        top.addWidget(self.btn_export)

        info = QVBoxLayout()
        info.addWidget(self.lbl_path)
        info.addWidget(self.lbl_summary)

        bottom = QHBoxLayout()
        bottom.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        bottom.addWidget(self.btn_close)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addSpacing(10)
        layout.addLayout(info)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Errores por fila:"))
        layout.addWidget(self.tbl_errors)
        layout.addLayout(bottom)
        self.setLayout(layout)

        # --- Signals ---
        self.btn_export.clicked.connect(self._on_export)
        self.btn_import.clicked.connect(self._on_import)
        self.btn_close.clicked.connect(self.close)

    def _on_export(self) -> None:
        self.export_requested.emit(self.cbo_entity.currentText())

    def _on_import(self) -> None:
        self.import_requested.emit(self.cbo_entity.currentText())

    # ------------------------------------------------------------
    # Render resultado import
    # ------------------------------------------------------------

    def set_result(self, *, entity: str, path: str, result: CsvImportResult) -> None:
        self.lbl_path.setText(f"Ruta: {path}")
        self.lbl_summary.setText(
            "Resumen: "
            f"{entity} → Creado: {result.created} | Actualizado: {result.updated} | Errores: {len(result.errors)}"
        )
        self._render_errors(result.errors)

    def _render_errors(self, errors: List[CsvRowError]) -> None:
        self.tbl_errors.setRowCount(0)

        for err in errors:
            r = self.tbl_errors.rowCount()
            self.tbl_errors.insertRow(r)

            self.tbl_errors.setItem(r, 0, QTableWidgetItem(str(err.row_number)))
            self.tbl_errors.setItem(r, 1, QTableWidgetItem(err.message))

            # Para que sea útil, mostrar hasta 3 campos/valores de la fila (resumen)
            raw = err.raw or {}
            keys = list(raw.keys())[:3]
            vals = [raw.get(k, "") for k in keys]

            self.tbl_errors.setItem(r, 2, QTableWidgetItem(", ".join(keys) if keys else "—"))
            self.tbl_errors.setItem(r, 3, QTableWidgetItem(" | ".join(vals) if vals else "—"))

        self.tbl_errors.resizeColumnsToContents()

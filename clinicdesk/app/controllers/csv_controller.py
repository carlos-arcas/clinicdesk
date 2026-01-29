# app/controllers/csv_controller.py
"""
Controlador UI para importar/exportar CSV.

Responsabilidades:
- Conectar UI con CsvService
- Manejar diálogos de archivo
- Mostrar resumen y errores

No contiene:
- Lógica CSV (eso está en application/csv/*)
- Lógica de repositorios
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Callable, Dict, Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from application.usecases.csv.csv_service import CsvService, CsvImportResult
from app.ui.dialog_csv import CsvDialog


class CsvController:
    def __init__(self, parent: QWidget, csv_service: CsvService) -> None:
        self._parent = parent
        self._svc = csv_service

        # Mapeo de entidades -> funciones service
        self._exporters: Dict[str, Callable[[str], None]] = {
            "Pacientes": self._svc.export_pacientes,
            "Médicos": self._svc.export_medicos,
            "Personal": self._svc.export_personal,
            "Medicamentos": self._svc.export_medicamentos,
            "Materiales": self._svc.export_materiales,
            "Salas": self._svc.export_salas,
        }

        self._importers: Dict[str, Callable[[str], CsvImportResult]] = {
            "Pacientes": self._svc.import_pacientes,
            "Médicos": self._svc.import_medicos,
            "Personal": self._svc.import_personal,
            "Medicamentos": self._svc.import_medicamentos,
            "Materiales": self._svc.import_materiales,
            "Salas": self._svc.import_salas,
        }

    def open_dialog(self) -> None:
        dlg = CsvDialog(self._parent, entities=list(self._exporters.keys()))
        dlg.export_requested.connect(lambda entity: self._export(entity, dlg))
        dlg.import_requested.connect(lambda entity: self._import(entity, dlg))
        dlg.exec()

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def _export(self, entity: str, dlg: CsvDialog) -> None:
        exporter = self._exporters.get(entity)
        if not exporter:
            QMessageBox.warning(self._parent, "CSV", f"Entidad no soportada: {entity}")
            return

        default_name = f"{entity.lower().replace('é','e').replace('í','i')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Exportar CSV",
            default_name,
            "CSV (*.csv);;Todos (*.*)",
        )
        if not path:
            return

        try:
            exporter(path)
            QMessageBox.information(self._parent, "CSV", f"Exportación completada:\n{path}")
        except Exception as e:
            QMessageBox.critical(self._parent, "CSV - Error", str(e))

    def _import(self, entity: str, dlg: CsvDialog) -> None:
        importer = self._importers.get(entity)
        if not importer:
            QMessageBox.warning(self._parent, "CSV", f"Entidad no soportada: {entity}")
            return

        path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Importar CSV",
            "",
            "CSV (*.csv);;Todos (*.*)",
        )
        if not path:
            return

        try:
            res = importer(path)
            dlg.set_result(entity=entity, path=path, result=res)

            # Mensaje resumen
            if res.errors:
                QMessageBox.warning(
                    self._parent,
                    "CSV - Importación con errores",
                    f"Importación finalizada.\n\n"
                    f"Creados: {res.created}\n"
                    f"Actualizados: {res.updated}\n"
                    f"Errores: {len(res.errors)}\n\n"
                    f"Revisa la tabla de errores.",
                )
            else:
                QMessageBox.information(
                    self._parent,
                    "CSV - Importación OK",
                    f"Importación completada.\n\n"
                    f"Creados: {res.created}\n"
                    f"Actualizados: {res.updated}\n"
                    f"Ruta: {path}",
                )

        except Exception as e:
            QMessageBox.critical(self._parent, "CSV - Error", str(e))

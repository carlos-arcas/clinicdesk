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

from typing import Callable, Dict, Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from clinicdesk.app.application.csv.csv_service import CsvService, CsvImportResult
from clinicdesk.app.pages.dialog_csv import CsvDialog
from clinicdesk.app.ui.error_presenter import present_error


class CsvController:
    def __init__(
        self,
        parent: QWidget,
        csv_service: CsvService,
        *,
        on_import_complete: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._parent = parent
        self._svc = csv_service
        self._on_import_complete = on_import_complete

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
            present_error(self._parent, e)

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
            if self._on_import_complete:
                self._on_import_complete(entity)

            summary = (
                "Importación completada: "
                f"Creado: {res.created} | Actualizado: {res.updated} | Errores: {len(res.errors)}"
            )
            if res.errors:
                details = "\n".join(
                    f"Fila {err.row_number}: {err.message} | {err.raw}"
                    for err in res.errors
                )
                msg_box = QMessageBox(self._parent)
                msg_box.setWindowTitle("CSV - Importación con errores")
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(summary)
                msg_box.setDetailedText(details)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
            else:
                QMessageBox.information(self._parent, "CSV - Importación OK", summary)

        except Exception as e:
            present_error(self._parent, e)

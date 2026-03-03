from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from clinicdesk.app.application.usecases.exportar_auditoria_csv import mapear_error_exportacion
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.pages.auditoria.persistencia_exportacion_settings import (
    clave_ultima_ruta_exportacion_auditoria,
    normalizar_ruta_sugerida_exportacion,
)

LOGGER = get_logger(__name__)


class ExportadorCsvAuditoria:
    def __init__(self, parent: QWidget, settings: QSettings, traductor) -> None:
        self._parent = parent
        self._settings = settings
        self._tr = traductor

    def confirmar(self, total: int) -> bool:
        msg = self._tr("auditoria.exportar.confirmacion").format(total=total)
        return QMessageBox.question(self._parent, self._tr("auditoria.titulo"), msg) == QMessageBox.Yes

    def guardar_con_reintento(self, csv_texto: str, total_filas: int, nombre_archivo: str, preset_rango: str | None) -> None:
        ruta_sugerida = self._ruta_sugerida(nombre_archivo)
        while True:
            ruta_guardado, _ = QFileDialog.getSaveFileName(self._parent, self._tr("auditoria.exportar.titulo_guardar"), ruta_sugerida, "CSV (*.csv)")
            if not ruta_guardado:
                return
            try:
                Path(ruta_guardado).write_text(csv_texto, encoding="utf-8")
            except OSError as exc:
                if not self._on_error_guardado(exc, total_filas, preset_rango, ruta_guardado):
                    return
                ruta_sugerida = ruta_guardado
                continue
            self._settings.setValue(clave_ultima_ruta_exportacion_auditoria(), str(Path(ruta_guardado).expanduser().resolve().parent))
            QMessageBox.information(self._parent, self._tr("auditoria.titulo"), self._tr("auditoria.export_ok"))
            return

    def _ruta_sugerida(self, nombre_archivo: str) -> str:
        ultima_ruta = self._settings.value(clave_ultima_ruta_exportacion_auditoria(), "", type=str)
        return normalizar_ruta_sugerida_exportacion(ultima_ruta or None, nombre_archivo)

    def _on_error_guardado(self, exc: OSError, total_filas: int, preset_rango: str | None, ruta_guardado: str) -> bool:
        reason_code = mapear_error_exportacion(exc)
        LOGGER.warning(
            "auditoria_export_fail",
            extra={
                "action": "auditoria_export_fail",
                "reason_code": reason_code,
                "total_filas": total_filas,
                "preset_rango": preset_rango or "none",
                "tiene_ruta": bool(ruta_guardado),
            },
        )
        return self._mostrar_error(reason_code, permitir_reintento=True)

    def mostrar_error(self, reason_code: str, *, permitir_reintento: bool) -> bool:
        return self._mostrar_error(reason_code, permitir_reintento=permitir_reintento)

    def _mostrar_error(self, reason_code: str, *, permitir_reintento: bool) -> bool:
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(self._tr("auditoria.export_error_titulo"))
        box.setText(self._tr(f"auditoria.export_error_texto_{reason_code}"))
        box.setInformativeText(self._tr(f"auditoria.export_error_sugerencia_{reason_code}"))
        cancelar = box.addButton(self._tr("auditoria.cancelar"), QMessageBox.RejectRole)
        reintentar = box.addButton(self._tr("auditoria.reintentar"), QMessageBox.AcceptRole) if permitir_reintento else None
        box.exec()
        return bool(permitir_reintento and box.clickedButton() == reintentar and box.clickedButton() is not cancelar)

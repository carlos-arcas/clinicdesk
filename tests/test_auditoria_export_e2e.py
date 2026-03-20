from __future__ import annotations

import csv
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    from clinicdesk.app.pages.auditoria.page import PageAuditoria
    from clinicdesk.app.ui.main_window import MainWindow
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso, EventoAuditoriaAcceso
from clinicdesk.app.application.usecases.exportar_auditoria_csv import COLUMNAS_EXPORTACION_AUDITORIA
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.auditoria.persistencia_exportacion_settings import clave_ultima_ruta_exportacion_auditoria

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


class _DialogosExportacionControlados:
    def __init__(self, ruta_guardado: Path) -> None:
        self.ruta_guardado = ruta_guardado

    def confirmar(self, *_args, **_kwargs) -> int:
        return QMessageBox.Yes

    def elegir_ruta(self, *_args, **_kwargs) -> tuple[str, str]:
        return self.ruta_guardado.as_posix(), "CSV (*.csv)"


def _registrar_evento(container, *, usuario: str, accion: AccionAuditoriaAcceso, entidad: EntidadAuditoriaAcceso, entidad_id: str) -> None:
    timestamp = datetime.now(UTC).isoformat()
    container.auditoria_accesos_repo.registrar(
        EventoAuditoriaAcceso(
            timestamp_utc=timestamp,
            usuario=usuario,
            modo_demo=False,
            accion=accion,
            entidad_tipo=entidad,
            entidad_id=entidad_id,
            metadata_json={"origen": "test_e2e_export_auditoria", "email": "oculto@example.com"},
        )
    )


def _abrir_page_auditoria(qtbot, container) -> tuple[MainWindow, PageAuditoria]:
    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)
    window.show()
    item = window._sidebar_item_by_key["auditoria"]
    window.sidebar.setCurrentRow(window.sidebar.row(item))
    qtbot.waitUntil(lambda: isinstance(window.stack.currentWidget(), PageAuditoria))
    page = window.stack.currentWidget()
    assert isinstance(page, PageAuditoria)
    return window, page


def _seleccionar_filtros_exportables(page: PageAuditoria, qtbot) -> None:
    page._ui.input_usuario.setText("")
    page._ui.combo_accion.setCurrentIndex(page._ui.combo_accion.findData(AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE.value))
    page._ui.combo_entidad.setCurrentIndex(page._ui.combo_entidad.findData(EntidadAuditoriaAcceso.PACIENTE.value))
    qtbot.mouseClick(page._ui.btn_buscar, Qt.LeftButton)


def _insertar_registro_integro_comprometido(connection) -> None:
    timestamp = datetime.now(UTC).isoformat()
    connection.execute(
        """
        INSERT INTO auditoria_accesos(
            timestamp_utc, usuario, modo_demo, accion, entidad_tipo, entidad_id,
            metadata_json, created_at_utc, prev_hash, entry_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            "intruso@example.com",
            0,
            AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE.value,
            EntidadAuditoriaAcceso.PACIENTE.value,
            "HC-ALTERADA-1",
            '{"origen":"corrupcion_controlada"}',
            timestamp,
            "hash_invalido",
            "hash_invalido",
        ),
    )
    connection.commit()


def test_exportar_auditoria_desde_page_real_genera_csv_saneado_y_feedback_ok(
    qtbot,
    container,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ruta_csv = tmp_path / "auditoria_ok.csv"
    dialogos = _DialogosExportacionControlados(ruta_csv)
    monkeypatch.setattr(QMessageBox, "question", dialogos.confirmar)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", dialogos.elegir_ruta)

    _registrar_evento(
        container,
        usuario="paciente@example.com",
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id="historia clinica HC-77881, dni=12345678Z",
    )
    _registrar_evento(
        container,
        usuario="recepcion@example.com",
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id="HC-99001",
    )

    window, page = _abrir_page_auditoria(qtbot, container)
    _seleccionar_filtros_exportables(page, qtbot)

    qtbot.waitUntil(lambda: page._ui.tabla.rowCount() == 2)
    textos_tabla = " ".join(
        page._ui.tabla.item(fila, columna).text()
        for fila in range(page._ui.tabla.rowCount())
        for columna in range(page._ui.tabla.columnCount())
        if page._ui.tabla.item(fila, columna) is not None
    )
    assert "paciente@example.com" not in textos_tabla
    assert "12345678Z" not in textos_tabla

    qtbot.mouseClick(page._ui.btn_exportar, Qt.LeftButton)

    qtbot.waitUntil(lambda: ruta_csv.exists())
    qtbot.waitUntil(lambda: window._toast_widget.isVisible())
    qtbot.waitUntil(lambda: window._toast_label.text() == window._i18n.t("job.done"))

    with ruta_csv.open(newline="", encoding="utf-8") as handle:
        data = list(csv.reader(handle))

    assert tuple(data[0]) == COLUMNAS_EXPORTACION_AUDITORIA
    assert set(data[0]) == set(COLUMNAS_EXPORTACION_AUDITORIA)
    csv_texto = ruta_csv.read_text(encoding="utf-8")
    assert "paciente@example.com" not in csv_texto
    assert "12345678Z" not in csv_texto
    assert "HC-77881" not in csv_texto
    assert "metadata_json" not in csv_texto
    assert "[REDACTED_EMAIL]" in csv_texto
    assert "[REDACTED_DNI_NIF]" in csv_texto
    assert "[REDACTED_HISTORIA_CLINICA]" in csv_texto
    assert str(ruta_csv.parent) in str(page._settings.value(clave_ultima_ruta_exportacion_auditoria(), ""))


def test_exportar_auditoria_desde_page_real_convierte_integridad_comprometida_en_feedback_controlado(
    qtbot,
    container,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ruta_csv = tmp_path / "auditoria_fail.csv"
    dialogos = _DialogosExportacionControlados(ruta_csv)
    monkeypatch.setattr(QMessageBox, "question", dialogos.confirmar)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", dialogos.elegir_ruta)

    _registrar_evento(
        container,
        usuario="auditor@example.com",
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id="HC-10001",
    )

    window, page = _abrir_page_auditoria(qtbot, container)
    _seleccionar_filtros_exportables(page, qtbot)
    qtbot.waitUntil(lambda: page._ui.tabla.rowCount() == 1)

    _insertar_registro_integro_comprometido(container.connection)

    qtbot.mouseClick(page._ui.btn_exportar, Qt.LeftButton)

    qtbot.waitUntil(lambda: window._toast_widget.isVisible())
    qtbot.waitUntil(lambda: window._toast_label.text() == window._i18n.t("job.failed"))
    assert ruta_csv.exists() is False

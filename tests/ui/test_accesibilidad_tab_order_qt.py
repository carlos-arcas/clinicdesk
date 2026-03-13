from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.ui_builder import build_confirmaciones_ui
from clinicdesk.app.pages.pacientes.ui_builder import build_pacientes_ui

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


def test_pacientes_ui_configura_nombres_accesibles_y_tab_order(qtbot) -> None:
    host = QWidget()
    qtbot.addWidget(host)
    ui = build_pacientes_ui(host, I18nManager("es"), can_write=True, headers=["id", "nombre"])

    assert ui.btn_nuevo.accessibleName()
    assert ui.btn_historial.toolTip()

    ui.filtros.txt_buscar.setFocus()
    qtbot.keyClick(ui.filtros.txt_buscar, "\t")
    assert host.focusWidget() is ui.filtros.cbo_estado


def test_confirmaciones_ui_configura_tab_order_busqueda_a_actualizar(qtbot) -> None:
    host = QWidget()
    qtbot.addWidget(host)
    ui = build_confirmaciones_ui(host, I18nManager("es"))

    assert ui.txt_buscar.isClearButtonEnabled()
    assert ui.table.accessibleName()

    ui.txt_buscar.setFocus()
    qtbot.keyClick(ui.txt_buscar, "\t")
    assert host.focusWidget() is ui.btn_actualizar

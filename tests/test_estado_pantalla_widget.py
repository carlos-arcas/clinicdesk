from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication, QLabel
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_estado_pantalla_widget_cambia_estados() -> None:
    _app()
    widget = EstadoPantallaWidget(I18nManager("es"))
    contenido = QLabel("contenido")

    widget.set_loading("ux_states.pacientes.loading")
    assert widget.estado_actual == "loading"

    widget.set_empty("ux_states.pacientes.empty", cta_text_key="ux_states.pacientes.cta_refresh")
    assert widget.estado_actual == "empty"

    widget.set_error("ux_states.pacientes.error", detalle_tecnico="RuntimeError", on_retry=lambda: None)
    assert widget.estado_actual == "error"

    widget.set_content(contenido)
    assert widget.estado_actual == "content"

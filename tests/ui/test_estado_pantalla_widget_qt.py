from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QLabel, QStackedWidget
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


def test_estado_pantalla_widget_muestra_vista_por_estado(qtbot) -> None:
    widget = EstadoPantallaWidget(I18nManager("es"))
    qtbot.addWidget(widget)
    stack = widget.findChild(QStackedWidget)
    assert stack is not None

    widget.set_loading("ux_states.pacientes.loading")
    assert widget.estado_actual == "loading"
    assert stack.currentWidget() is not None

    widget.set_empty("ux_states.pacientes.empty", cta_text_key="ux_states.pacientes.cta_refresh")
    assert widget.estado_actual == "empty"
    assert stack.currentWidget() is not None

    widget.set_error("ux_states.pacientes.error", detalle_tecnico="RuntimeError", on_retry=lambda: None)
    assert widget.estado_actual == "error"
    assert stack.currentWidget() is not None

    contenido = QLabel("contenido", widget)
    widget.set_content(contenido)
    assert widget.estado_actual == "content"
    assert stack.currentWidget() is contenido

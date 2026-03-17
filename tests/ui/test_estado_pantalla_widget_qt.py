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


@pytest.mark.ui
@pytest.mark.uiqt
def test_estado_pantalla_widget_set_processing_y_focus_retry(qtbot) -> None:
    widget = EstadoPantallaWidget(I18nManager("es"))
    qtbot.addWidget(widget)

    widget.set_processing("ux_states.processing.default")
    assert widget.estado_actual == "processing"

    widget.set_error("ux_states.pacientes.error", on_retry=lambda: None)
    assert widget.estado_actual == "error"
    assert widget.focusWidget() is not None


def test_estado_pantalla_widget_no_duplica_ni_huerfana_contenido(qtbot) -> None:
    widget = EstadoPantallaWidget(I18nManager("es"))
    qtbot.addWidget(widget)
    stack = widget.findChild(QStackedWidget)
    assert stack is not None

    contenido_a = QLabel("a", widget)
    contenido_b = QLabel("b", widget)

    widget.set_content(contenido_a)
    assert stack.indexOf(contenido_a) != -1

    widget.set_content(contenido_b)
    assert stack.indexOf(contenido_a) == -1
    assert contenido_a.parent() is None
    assert stack.indexOf(contenido_b) != -1


def test_estado_pantalla_widget_difiere_mutacion_fuera_hilo_gui(qtbot, monkeypatch) -> None:
    widget = EstadoPantallaWidget(I18nManager("es"))
    qtbot.addWidget(widget)
    widget.set_error("ux_states.pacientes.error")

    registro: list[str] = []
    widget.solicitar_loading.connect(lambda key: registro.append(key))
    monkeypatch.setattr(widget, "_permitir_mutacion_estado", lambda **_kwargs: False)

    widget.set_loading("ux_states.pacientes.loading")

    assert registro == ["ux_states.pacientes.loading"]
    assert widget.estado_actual == "error"

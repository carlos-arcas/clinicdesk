from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QLabel
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui.ux.estados_listado import ConfigEstadoListado, aplicar_estado_listado
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


@pytest.mark.ui
@pytest.mark.uiqt
def test_aplicar_estado_listado_transicion_loading_empty_error_ready(qtbot) -> None:
    widget = EstadoPantallaWidget(I18nManager("es"))
    qtbot.addWidget(widget)
    contenido = QLabel("tabla", widget)
    items_renderizados: list[object] = []

    def _render(rows: list[object]) -> None:
        items_renderizados[:] = rows

    config = ConfigEstadoListado(
        loading_key="ux_states.pacientes.loading",
        empty_key="ux_states.pacientes.empty",
        empty_cta_key="ux_states.pacientes.cta_refresh",
        error_key="ux_states.pacientes.error",
    )

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.LOADING),
        contenido=contenido,
        config=config,
        on_retry=lambda: None,
        render_rows=_render,
    )
    assert widget.estado_actual == "loading"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.EMPTY, items=[]),
        contenido=contenido,
        config=config,
        on_retry=lambda: None,
        render_rows=_render,
    )
    assert widget.estado_actual == "empty"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.ERROR, error_key="ux_states.pacientes.error"),
        contenido=contenido,
        config=config,
        on_retry=lambda: None,
        render_rows=_render,
    )
    assert widget.estado_actual == "error"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.CONTENT, items=[{"id": 1}]),
        contenido=contenido,
        config=config,
        on_retry=lambda: None,
        render_rows=_render,
    )
    assert widget.estado_actual == "content"
    assert items_renderizados == [{"id": 1}]

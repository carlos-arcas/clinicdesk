from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.ui.ux.estados_listado import ConfigEstadoListado, aplicar_estado_listado
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla


@dataclass
class SpyEstadoPantalla:
    estado_actual: str | None = None
    message_key: str | None = None

    def set_loading(self, message_key: str) -> None:
        self.estado_actual = "loading"
        self.message_key = message_key

    def set_error(self, message_key: str, *, on_retry=None) -> None:
        self.estado_actual = "error"
        self.message_key = message_key

    def set_empty(self, message_key: str, *, cta_text_key=None, on_cta=None) -> None:
        self.estado_actual = "empty"
        self.message_key = message_key

    def set_ready(self, contenido: object) -> None:
        self.estado_actual = "ready"
        self.message_key = None


def _config() -> ConfigEstadoListado:
    return ConfigEstadoListado(
        loading_key="ux_states.pacientes.loading",
        empty_key="ux_states.pacientes.empty",
        empty_filtered_key="ux_states.pacientes.empty_filtered",
        empty_cta_key="ux_states.pacientes.cta_refresh",
        error_key="ux_states.pacientes.error",
    )


def test_aplicar_estado_listado_error_y_loading() -> None:
    widget = SpyEstadoPantalla()

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.LOADING),
        contenido=object(),
        config=_config(),
        on_retry=lambda: None,
        render_rows=lambda _: None,
    )
    assert widget.estado_actual == "loading"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.ERROR, error_key="x.error"),
        contenido=object(),
        config=_config(),
        on_retry=lambda: None,
        render_rows=lambda _: None,
    )
    assert widget.estado_actual == "error"
    assert widget.message_key == "x.error"


def test_aplicar_estado_listado_empty_real_vs_filtrado_y_ready() -> None:
    widget = SpyEstadoPantalla()
    items_renderizados: list[object] = []

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.EMPTY, items=[], filtro_texto=""),
        contenido=object(),
        config=_config(),
        on_retry=lambda: None,
        render_rows=items_renderizados.extend,
    )
    assert widget.estado_actual == "empty"
    assert widget.message_key == "ux_states.pacientes.empty"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.EMPTY, items=[], filtro_texto="ana"),
        contenido=object(),
        config=_config(),
        on_retry=lambda: None,
        render_rows=items_renderizados.extend,
    )
    assert widget.estado_actual == "empty"
    assert widget.message_key == "ux_states.pacientes.empty_filtered"

    aplicar_estado_listado(
        estado_widget=widget,
        estado=EstadoListado(estado_pantalla=EstadoPantalla.CONTENT, items=[{"id": 1}]),
        contenido=object(),
        config=_config(),
        on_retry=lambda: None,
        render_rows=items_renderizados.extend,
    )
    assert widget.estado_actual == "ready"
    assert items_renderizados == [{"id": 1}]

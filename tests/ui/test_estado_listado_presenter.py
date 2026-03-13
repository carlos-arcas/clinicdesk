from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.ui.viewmodels.estado_listado_presenter import EstadoListadoPresenter
from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla


@dataclass
class _FakeWidgetEstado:
    ultimo_estado: str | None = None
    ultimo_mensaje: str | None = None

    def set_loading(self, key: str) -> None:
        self.ultimo_estado = "loading"
        self.ultimo_mensaje = key

    def set_processing(self, key: str) -> None:
        self.ultimo_estado = "processing"
        self.ultimo_mensaje = key

    def set_empty(self, key: str, *, cta_text_key: str | None = None, on_cta=None) -> None:
        self.ultimo_estado = "empty"
        self.ultimo_mensaje = f"{key}|{cta_text_key}"

    def set_error(self, key: str, *, on_retry=None, detalle_tecnico: str | None = None) -> None:
        self.ultimo_estado = "error"
        self.ultimo_mensaje = key

    def set_content(self, _widget: object) -> None:
        self.ultimo_estado = "content"
        self.ultimo_mensaje = None


def _build_presenter(widget: _FakeWidgetEstado) -> EstadoListadoPresenter[int]:
    return EstadoListadoPresenter[int](
        estado_widget=widget,
        contenido=object(),
        mensaje_loading_key="k.loading",
        mensaje_empty_key="k.empty",
        mensaje_error_default_key="k.error",
        cta_refresh_key="k.retry",
        mensaje_processing_key="k.processing",
    )


def test_presenter_renderiza_loading_y_processing() -> None:
    widget = _FakeWidgetEstado()
    presenter = _build_presenter(widget)

    presenter.render(
        EstadoListado[int](estado_pantalla=EstadoPantalla.LOADING), on_retry=lambda: None, render_rows=lambda _: None
    )
    assert widget.ultimo_estado == "loading"
    assert widget.ultimo_mensaje == "k.loading"

    presenter.render(
        EstadoListado[int](estado_pantalla=EstadoPantalla.PROCESSING), on_retry=lambda: None, render_rows=lambda _: None
    )
    assert widget.ultimo_estado == "processing"
    assert widget.ultimo_mensaje == "k.processing"


def test_presenter_renderiza_empty_error_y_content() -> None:
    widget = _FakeWidgetEstado()
    presenter = _build_presenter(widget)
    render_calls: list[list[int]] = []

    presenter.render(
        EstadoListado[int](estado_pantalla=EstadoPantalla.EMPTY, items=[]),
        on_retry=lambda: None,
        render_rows=render_calls.append,
    )
    assert widget.ultimo_estado == "empty"

    presenter.render(
        EstadoListado[int](estado_pantalla=EstadoPantalla.ERROR, error_key="k.error.custom"),
        on_retry=lambda: None,
        render_rows=render_calls.append,
    )
    assert widget.ultimo_estado == "error"
    assert widget.ultimo_mensaje == "k.error.custom"

    presenter.render(
        EstadoListado[int](estado_pantalla=EstadoPantalla.CONTENT, items=[1, 2]),
        on_retry=lambda: None,
        render_rows=render_calls.append,
    )
    assert widget.ultimo_estado == "content"
    assert render_calls[-1] == [1, 2]

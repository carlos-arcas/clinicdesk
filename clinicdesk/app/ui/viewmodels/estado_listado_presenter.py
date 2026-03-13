from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from typing import Protocol

from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla

ItemT = TypeVar("ItemT")


class EstadoPantallaPort(Protocol):
    def set_loading(self, key: str) -> None: ...

    def set_processing(self, key: str) -> None: ...

    def set_empty(
        self, key: str, *, cta_text_key: str | None = None, on_cta: Callable[[], None] | None = None
    ) -> None: ...

    def set_error(
        self, key: str, *, detalle_tecnico: str | None = None, on_retry: Callable[[], None] | None = None
    ) -> None: ...

    def set_content(self, widget: object) -> None: ...


class EstadoListadoPresenter(Generic[ItemT]):
    def __init__(
        self,
        *,
        estado_widget: EstadoPantallaPort,
        contenido: object,
        mensaje_loading_key: str,
        mensaje_empty_key: str,
        mensaje_error_default_key: str,
        cta_refresh_key: str,
        mensaje_processing_key: str,
    ) -> None:
        self._estado_widget = estado_widget
        self._contenido = contenido
        self._mensaje_loading_key = mensaje_loading_key
        self._mensaje_empty_key = mensaje_empty_key
        self._mensaje_error_default_key = mensaje_error_default_key
        self._cta_refresh_key = cta_refresh_key
        self._mensaje_processing_key = mensaje_processing_key

    def render(
        self,
        estado: EstadoListado[ItemT],
        *,
        on_retry: Callable[[], None],
        render_rows: Callable[[list[ItemT]], None],
    ) -> None:
        if estado.estado_pantalla is EstadoPantalla.LOADING:
            self._estado_widget.set_loading(self._mensaje_loading_key)
            return
        if estado.estado_pantalla is EstadoPantalla.PROCESSING:
            self._estado_widget.set_processing(self._mensaje_processing_key)
            return
        if estado.estado_pantalla is EstadoPantalla.ERROR:
            self._estado_widget.set_error(estado.error_key or self._mensaje_error_default_key, on_retry=on_retry)
            return
        render_rows(estado.items)
        if estado.estado_pantalla is EstadoPantalla.EMPTY:
            self._estado_widget.set_empty(self._mensaje_empty_key, cta_text_key=self._cta_refresh_key, on_cta=on_retry)
            return
        self._estado_widget.set_content(self._contenido)

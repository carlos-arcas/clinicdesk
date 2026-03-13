from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla
from clinicdesk.app.ui.widgets.estado_pantalla_widget import EstadoPantallaWidget


@dataclass(frozen=True, slots=True)
class ConfigEstadoListado:
    loading_key: str
    empty_key: str
    empty_cta_key: str
    error_key: str


def aplicar_estado_listado(
    *,
    estado_widget: EstadoPantallaWidget,
    estado: EstadoListado[object],
    contenido,
    config: ConfigEstadoListado,
    on_retry: Callable[[], None],
    render_rows: Callable[[list[object]], None],
) -> None:
    if estado.estado_pantalla is EstadoPantalla.LOADING:
        estado_widget.set_loading(config.loading_key)
        return
    if estado.estado_pantalla is EstadoPantalla.ERROR:
        estado_widget.set_error(estado.error_key or config.error_key, on_retry=on_retry)
        return

    render_rows(estado.items)
    if estado.estado_pantalla is EstadoPantalla.EMPTY:
        estado_widget.set_empty(config.empty_key, cta_text_key=config.empty_cta_key, on_cta=on_retry)
        return

    estado_widget.set_ready(contenido)

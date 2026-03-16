from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from clinicdesk.app.ui.viewmodels.contratos import EstadoListado, EstadoPantalla


class PuertoEstadoPantalla(Protocol):
    def set_loading(self, message_key: str) -> None: ...

    def set_error(self, message_key: str, *, on_retry: Callable[[], None] | None = None) -> None: ...

    def set_empty(
        self,
        message_key: str,
        *,
        cta_text_key: str | None = None,
        on_cta: Callable[[], None] | None = None,
    ) -> None: ...

    def set_ready(self, contenido: object) -> None: ...


@dataclass(frozen=True, slots=True)
class ConfigEstadoListado:
    loading_key: str
    empty_key: str
    empty_cta_key: str
    error_key: str
    empty_filtered_key: str | None = None


def resolver_clave_empty(estado: EstadoListado[object], *, config: ConfigEstadoListado) -> str:
    if config.empty_filtered_key and estado.filtro_texto.strip():
        return config.empty_filtered_key
    return config.empty_key


def aplicar_estado_listado(
    *,
    estado_widget: PuertoEstadoPantalla,
    estado: EstadoListado[object],
    contenido: object,
    config: ConfigEstadoListado,
    on_retry: Callable[[], None],
    render_rows: Callable[[list[object]], None],
) -> None:
    if estado.estado_pantalla is EstadoPantalla.LOADING:
        if getattr(estado_widget, "estado_actual", None) != "loading":
            estado_widget.set_loading(config.loading_key)
        return
    if estado.estado_pantalla is EstadoPantalla.ERROR:
        estado_widget.set_error(estado.error_key or config.error_key, on_retry=on_retry)
        return

    render_rows(estado.items)
    if estado.estado_pantalla is EstadoPantalla.EMPTY:
        estado_widget.set_empty(
            resolver_clave_empty(estado, config=config),
            cta_text_key=config.empty_cta_key,
            on_cta=on_retry,
        )
        return

    estado_widget.set_ready(contenido)

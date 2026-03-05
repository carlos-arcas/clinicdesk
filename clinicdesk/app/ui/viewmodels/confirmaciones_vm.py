from __future__ import annotations

from collections.abc import Callable
from typing import Any

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text
from clinicdesk.app.ui.viewmodels.contratos import EventoUI
from clinicdesk.app.ui.viewmodels.listado_base import ListadoViewModelBase


ListarConfirmacionesFn = Callable[..., list[Any]]
SuscriptorEvento = Callable[[EventoUI], None]


class ConfirmacionesViewModel(ListadoViewModelBase[Any]):
    def __init__(self, listar_confirmaciones: ListarConfirmacionesFn) -> None:
        super().__init__()
        self._listar_confirmaciones = listar_confirmaciones
        self._suscriptores_evento: list[SuscriptorEvento] = []
        self._rango = "7D"
        self._estado_filtro = "TODOS"

    def subscribe_eventos(self, callback: SuscriptorEvento) -> Callable[[], None]:
        self._suscriptores_evento.append(callback)

        def unsubscribe() -> None:
            if callback in self._suscriptores_evento:
                self._suscriptores_evento.remove(callback)

        return unsubscribe

    def cargar(self) -> None:
        self.set_loading()
        try:
            items = self._listar_confirmaciones(
                filtro_texto=self.estado.filtro_texto,
                rango=self._rango,
                estado=self._estado_filtro,
            )
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.confirmaciones.error")
            return
        self.set_items(items)

    def aplicar_filtro(self, texto: str) -> None:
        filtro = self.normalizar_filtro(texto, to_lower=False)
        self.estado.filtro_texto = filtro
        self.estado.last_search_safe = sanitize_search_text(filtro)
        self.cargar()

    def refrescar(self) -> None:
        self.set_loading()
        try:
            items = self._listar_confirmaciones(
                filtro_texto=self.estado.filtro_texto,
                rango=self._rango,
                estado=self._estado_filtro,
            )
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.confirmaciones.error")
            self._emit_evento("toast", {"key": "toast.refresh_fail"})
            return
        self.set_items(items)
        if not items:
            self._emit_evento("toast", {"key": "toast.refresh_empty_confirmaciones"})
        self._emit_evento("toast", {"key": "toast.refresh_ok_confirmaciones"})

    def actualizar_contexto(self, *, rango: str, estado: str, texto: str) -> None:
        self._rango = rango
        self._estado_filtro = estado
        self.estado.filtro_texto = self.normalizar_filtro(texto, to_lower=False)
        self.estado.last_search_safe = sanitize_search_text(self.estado.filtro_texto)

    def seleccionar(self, cita_id: int | None) -> None:
        self.estado.seleccion_id = cita_id
        self._emit()

    def ir_a(self, cita_id: int) -> None:
        self._emit_evento("nav", {"cita_id": cita_id})

    def resolver_carga_ok(self, *, rows: list[Any], emitir_toast: bool) -> None:
        self.set_items(rows)
        if emitir_toast and not rows:
            self._emit_evento("toast", {"key": "toast.refresh_empty_confirmaciones"})
        if emitir_toast:
            self._emit_evento("toast", {"key": "toast.refresh_ok_confirmaciones"})

    def resolver_carga_error(self, *, error_key: str, emitir_toast: bool) -> None:
        self.set_error(error_key)
        if emitir_toast:
            self._emit_evento("toast", {"key": "toast.refresh_fail"})

    def _emit_evento(self, tipo: str, payload: dict[str, object]) -> None:
        evento = EventoUI(tipo=tipo, payload=payload)
        for callback in tuple(self._suscriptores_evento):
            callback(evento)

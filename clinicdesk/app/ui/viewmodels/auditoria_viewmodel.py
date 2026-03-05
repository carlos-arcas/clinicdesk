from __future__ import annotations

from collections.abc import Callable
from typing import Any

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text
from clinicdesk.app.ui.viewmodels.contratos import EventoUI
from clinicdesk.app.ui.viewmodels.listado_base import ListadoViewModelBase

ListarAuditoriaFn = Callable[[str], list[Any]]
SuscriptorEvento = Callable[[EventoUI], None]


class AuditoriaViewModel(ListadoViewModelBase[Any]):
    """Movido desde PageAuditoria: carga/refresh, filtro normalizado, selección y eventos UI."""

    def __init__(self, listar_auditoria: ListarAuditoriaFn) -> None:
        super().__init__()
        self._listar_auditoria = listar_auditoria
        self._suscriptores_evento: list[SuscriptorEvento] = []

    def subscribe_eventos(self, callback: SuscriptorEvento) -> Callable[[], None]:
        self._suscriptores_evento.append(callback)

        def unsubscribe() -> None:
            if callback in self._suscriptores_evento:
                self._suscriptores_evento.remove(callback)

        return unsubscribe

    def cargar(self) -> None:
        self.set_loading()
        try:
            items = self._listar_auditoria(self.estado.filtro_texto)
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.auditoria.error")
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
            items = self._listar_auditoria(self.estado.filtro_texto)
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.auditoria.error")
            self._emit_evento("toast", {"key": "toast.refresh_fail"})
            return
        self.set_items(items)
        if not items:
            self._emit_evento("toast", {"key": "toast.refresh_empty_auditoria"})
        self._emit_evento("toast", {"key": "toast.refresh_ok_auditoria"})

    def seleccionar(self, item_id: int | None) -> None:
        self.estado.seleccion_id = item_id
        self._emit()

    def exportar_csv(self) -> None:
        self._emit_evento("job", {"accion": "exportar_auditoria_csv"})

    def _emit_evento(self, tipo: str, payload: dict[str, object]) -> None:
        evento = EventoUI(tipo=tipo, payload=payload)
        for callback in tuple(self._suscriptores_evento):
            callback(evento)

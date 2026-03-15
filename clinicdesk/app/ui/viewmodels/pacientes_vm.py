from __future__ import annotations

from collections.abc import Callable

from clinicdesk.app.application.preferencias.preferencias_usuario import sanitize_search_text
from clinicdesk.app.queries.pacientes_queries import PacienteRow
from clinicdesk.app.ui.viewmodels.contratos import EventoUI
from clinicdesk.app.ui.viewmodels.listado_base import ListadoViewModelBase


ListarPacientesFn = Callable[[bool, str], list[PacienteRow]]
SuscriptorEvento = Callable[[EventoUI], None]


class PacientesViewModel(ListadoViewModelBase[PacienteRow]):
    def __init__(self, listar_pacientes: ListarPacientesFn) -> None:
        super().__init__()
        self._listar_pacientes = listar_pacientes
        self._suscriptores_evento: list[SuscriptorEvento] = []
        self._activo = True

    def subscribe_eventos(self, callback: SuscriptorEvento) -> Callable[[], None]:
        self._suscriptores_evento.append(callback)

        def unsubscribe() -> None:
            if callback in self._suscriptores_evento:
                self._suscriptores_evento.remove(callback)

        return unsubscribe

    def cargar(self) -> None:
        self.set_loading()
        try:
            items = self._listar_pacientes(self._activo, self.estado.filtro_texto)
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.pacientes.error")
            return
        self.set_items(items)

    def aplicar_filtro(self, texto: str | None) -> None:
        filtro = self.normalizar_filtro(texto, to_lower=False)
        self.estado.filtro_texto = filtro
        self.estado.last_search_safe = sanitize_search_text(filtro)
        self.cargar()

    def refrescar(self) -> None:
        self.set_loading()
        try:
            items = self._listar_pacientes(self._activo, self.estado.filtro_texto)
        except Exception:  # noqa: BLE001
            self.set_error("ux_states.pacientes.error")
            self._emit_evento("toast", {"key": "toast.refresh_fail"})
            return
        self.set_items(items)
        self._emit_evento("toast", {"key": "toast.refresh_ok_pacientes"})

    def seleccionar(self, paciente_id: int | None) -> None:
        self.estado.seleccion_id = paciente_id
        self._emit()

    def actualizar_contexto(self, *, activo: bool, texto: str | None, seleccion_id: int | None) -> None:
        self._activo = activo
        self.estado.filtro_texto = self.normalizar_filtro(texto, to_lower=False)
        self.estado.last_search_safe = sanitize_search_text(self.estado.filtro_texto)
        self.estado.seleccion_id = seleccion_id

    def resolver_carga_ok(self, *, rows: list[PacienteRow], emitir_toast: bool) -> None:
        self.set_items(rows)
        if emitir_toast:
            self._emit_evento("toast", {"key": "toast.refresh_ok_pacientes"})

    def resolver_carga_error(self, *, error_key: str, emitir_toast: bool) -> None:
        self.set_error(error_key)
        if emitir_toast:
            self._emit_evento("toast", {"key": "toast.refresh_fail"})

    def _emit_evento(self, tipo: str, payload: dict[str, object]) -> None:
        evento = EventoUI(tipo=tipo, payload=payload)
        for callback in tuple(self._suscriptores_evento):
            callback(evento)

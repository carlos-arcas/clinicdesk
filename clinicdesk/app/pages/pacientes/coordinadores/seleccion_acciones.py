from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from clinicdesk.app.pages.pacientes.helpers.estado_acciones_pacientes import EstadoAccionesPacientes


class _TablaSeleccionable(Protocol):
    def currentRow(self) -> int: ...
    def item(self, row: int, column: int): ...
    def rowCount(self) -> int: ...
    def setCurrentCell(self, row: int, column: int) -> None: ...


class _BotonAccion(Protocol):
    def setEnabled(self, enabled: bool) -> None: ...


class _UISeleccionPacientes(Protocol):
    table: _TablaSeleccionable
    btn_nuevo: _BotonAccion
    btn_editar: _BotonAccion
    btn_desactivar: _BotonAccion
    btn_historial: _BotonAccion


class CoordinadorSeleccionAccionesPacientes:
    def __init__(
        self,
        *,
        ui: _UISeleccionPacientes,
        can_write: bool,
        set_buttons_enabled: Callable[..., None],
    ) -> None:
        self._ui = ui
        self._can_write = can_write
        self._set_buttons_enabled = set_buttons_enabled

    def estado_actual(self) -> EstadoAccionesPacientes:
        return EstadoAccionesPacientes(selected_id=self._selected_id(), can_write=self._can_write)

    def actualizar_botones(self) -> EstadoAccionesPacientes:
        estado = self.estado_actual()
        self._ui.btn_nuevo.setEnabled(estado.permite_nuevo)
        if self._can_write:
            self._set_buttons_enabled(
                has_selection=estado.has_selection,
                buttons=[self._ui.btn_editar, self._ui.btn_desactivar],
            )
        else:
            self._ui.btn_editar.setEnabled(False)
            self._ui.btn_desactivar.setEnabled(False)
        self._ui.btn_historial.setEnabled(estado.permite_historial)
        return estado

    def seleccionar_por_id(self, paciente_id: int) -> None:
        for row in range(self._ui.table.rowCount()):
            item = self._ui.table.item(row, 0)
            if item and item.text() == str(paciente_id):
                self._ui.table.setCurrentCell(row, 0)
                return

    def preparar_context_menu(self, row: int | None) -> EstadoAccionesPacientes:
        if row is not None and row >= 0:
            self._ui.table.setCurrentCell(row, 0)
        return self.actualizar_botones()

    def _selected_id(self) -> int | None:
        current_row = self._ui.table.currentRow()
        if current_row < 0:
            return None
        item = self._ui.table.item(current_row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

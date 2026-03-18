from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class AccionPaciente(str, Enum):
    NUEVO = "nuevo"
    EDITAR = "editar"
    DESACTIVAR = "desactivar"
    HISTORIAL = "historial"


@dataclass(frozen=True, slots=True)
class EstadoAccionesPacientes:
    selected_id: int | None
    can_write: bool

    @property
    def has_selection(self) -> bool:
        return self.selected_id is not None

    @property
    def permite_nuevo(self) -> bool:
        return self.can_write

    @property
    def permite_editar(self) -> bool:
        return self.can_write and self.has_selection

    @property
    def permite_desactivar(self) -> bool:
        return self.can_write and self.has_selection

    @property
    def permite_historial(self) -> bool:
        return self.has_selection


def accion_habilitada(*, accion: AccionPaciente, estado: EstadoAccionesPacientes) -> bool:
    if accion is AccionPaciente.NUEVO:
        return estado.permite_nuevo
    if accion is AccionPaciente.EDITAR:
        return estado.permite_editar
    if accion is AccionPaciente.DESACTIVAR:
        return estado.permite_desactivar
    return estado.permite_historial


def despachar_accion(
    *,
    accion: AccionPaciente | None,
    on_nuevo_cb: Callable[[], None],
    on_editar_cb: Callable[[], None],
    on_desactivar_cb: Callable[[], None],
    on_historial_cb: Callable[[], None],
) -> None:
    if accion is AccionPaciente.NUEVO:
        on_nuevo_cb()
    elif accion is AccionPaciente.EDITAR:
        on_editar_cb()
    elif accion is AccionPaciente.DESACTIVAR:
        on_desactivar_cb()
    elif accion is AccionPaciente.HISTORIAL:
        on_historial_cb()

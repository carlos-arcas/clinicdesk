from __future__ import annotations

from types import SimpleNamespace

from clinicdesk.app.pages.pacientes.coordinadores.seleccion_acciones import CoordinadorSeleccionAccionesPacientes
from clinicdesk.app.pages.pacientes.helpers.estado_acciones_pacientes import (
    AccionPaciente,
    EstadoAccionesPacientes,
    accion_habilitada,
    despachar_accion,
)


class _Item:
    def __init__(self, value: str) -> None:
        self._value = value

    def text(self) -> str:
        return self._value


class _TablaFake:
    def __init__(self, ids: list[int]) -> None:
        self._ids = ids
        self._current_row = -1

    def currentRow(self) -> int:
        return self._current_row

    def item(self, row: int, column: int):
        if column != 0 or row < 0 or row >= len(self._ids):
            return None
        return _Item(str(self._ids[row]))

    def rowCount(self) -> int:
        return len(self._ids)

    def setCurrentCell(self, row: int, column: int) -> None:
        assert column == 0
        self._current_row = row


class _BotonFake:
    def __init__(self) -> None:
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


class _BotonesHabilitadosSpy:
    def __init__(self) -> None:
        self.llamadas: list[tuple[bool, list[object]]] = []

    def __call__(self, *, has_selection: bool, buttons: list[object]) -> None:
        self.llamadas.append((has_selection, buttons))
        for boton in buttons:
            boton.setEnabled(has_selection)


def _crear_ui() -> SimpleNamespace:
    return SimpleNamespace(
        table=_TablaFake([101, 202]),
        btn_nuevo=_BotonFake(),
        btn_editar=_BotonFake(),
        btn_desactivar=_BotonFake(),
        btn_historial=_BotonFake(),
    )


def test_coordinador_actualiza_botones_segun_seleccion_y_permisos() -> None:
    ui = _crear_ui()
    spy = _BotonesHabilitadosSpy()
    coordinador = CoordinadorSeleccionAccionesPacientes(ui=ui, can_write=True, set_buttons_enabled=spy)

    estado_inicial = coordinador.actualizar_botones()

    assert estado_inicial.selected_id is None
    assert ui.btn_nuevo.enabled is True
    assert ui.btn_editar.enabled is False
    assert ui.btn_desactivar.enabled is False
    assert ui.btn_historial.enabled is False

    ui.table.setCurrentCell(1, 0)
    estado = coordinador.actualizar_botones()

    assert estado.selected_id == 202
    assert ui.btn_editar.enabled is True
    assert ui.btn_desactivar.enabled is True
    assert ui.btn_historial.enabled is True
    assert spy.llamadas[-1][0] is True


def test_coordinador_context_menu_solo_habilita_historial_en_modo_lectura() -> None:
    ui = _crear_ui()
    spy = _BotonesHabilitadosSpy()
    coordinador = CoordinadorSeleccionAccionesPacientes(ui=ui, can_write=False, set_buttons_enabled=spy)

    estado = coordinador.preparar_context_menu(0)

    assert estado.selected_id == 101
    assert ui.table.currentRow() == 0
    assert ui.btn_nuevo.enabled is False
    assert ui.btn_editar.enabled is False
    assert ui.btn_desactivar.enabled is False
    assert ui.btn_historial.enabled is True
    assert spy.llamadas == []


def test_estado_acciones_y_dispatch_se_mantienen_coherentes() -> None:
    estado = EstadoAccionesPacientes(selected_id=101, can_write=False)

    assert accion_habilitada(accion=AccionPaciente.NUEVO, estado=estado) is False
    assert accion_habilitada(accion=AccionPaciente.EDITAR, estado=estado) is False
    assert accion_habilitada(accion=AccionPaciente.DESACTIVAR, estado=estado) is False
    assert accion_habilitada(accion=AccionPaciente.HISTORIAL, estado=estado) is True

    llamadas: list[str] = []
    despachar_accion(
        accion=AccionPaciente.HISTORIAL,
        on_nuevo_cb=lambda: llamadas.append("nuevo"),
        on_editar_cb=lambda: llamadas.append("editar"),
        on_desactivar_cb=lambda: llamadas.append("desactivar"),
        on_historial_cb=lambda: llamadas.append("historial"),
    )

    assert llamadas == ["historial"]

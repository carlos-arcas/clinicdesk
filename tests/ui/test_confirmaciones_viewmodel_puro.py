from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.ui.viewmodels.confirmaciones_vm import ConfirmacionesViewModel
from clinicdesk.app.ui.viewmodels.contratos import EstadoPantalla


@dataclass(slots=True)
class ConfirmacionRowFake:
    cita_id: int


def test_cargar_transicion_loading_content() -> None:
    vm = ConfirmacionesViewModel(lambda **_kwargs: [ConfirmacionRowFake(cita_id=1), ConfirmacionRowFake(cita_id=2)])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.CONTENT]


def test_cargar_transicion_loading_empty() -> None:
    vm = ConfirmacionesViewModel(lambda **_kwargs: [])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.EMPTY]


def test_cargar_transicion_loading_error() -> None:
    def _rompe(**_kwargs):
        raise RuntimeError("boom")

    vm = ConfirmacionesViewModel(_rompe)
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.ERROR]
    assert vm.estado.error_key == "ux_states.confirmaciones.error"


def test_refrescar_emite_toast_empty_y_ok() -> None:
    vm = ConfirmacionesViewModel(lambda **_kwargs: [])
    eventos: list[str] = []
    vm.subscribe_eventos(lambda evento: eventos.append(str(evento.payload.get("key"))))

    vm.refrescar()

    assert eventos == ["toast.refresh_empty_confirmaciones", "toast.refresh_ok_confirmaciones"]


def test_refrescar_emite_toast_fail_si_excepcion() -> None:
    vm = ConfirmacionesViewModel(lambda **_kwargs: 1 / 0)
    eventos: list[str] = []
    vm.subscribe_eventos(lambda evento: eventos.append(str(evento.payload.get("key"))))

    vm.refrescar()

    assert eventos == ["toast.refresh_fail"]


def test_seleccionar_e_ir_a_actualizan_estado_y_evento_nav() -> None:
    vm = ConfirmacionesViewModel(lambda **_kwargs: [])
    nav: list[object] = []
    vm.subscribe_eventos(lambda evento: nav.append(evento.payload.get("cita_id")) if evento.tipo == "nav" else None)

    vm.seleccionar(33)
    vm.ir_a(77)

    assert vm.estado.seleccion_id == 33
    assert nav == [77]

from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.ui.viewmodels.contratos import EstadoPantalla
from clinicdesk.app.ui.viewmodels.pacientes_vm import PacientesViewModel


@dataclass(slots=True)
class PacienteRowFake:
    id: int
    nombre: str


def test_cargar_emite_loading_y_content() -> None:
    vm = PacientesViewModel(lambda _activo, _texto: [PacienteRowFake(id=7, nombre="Ana")])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.CONTENT]
    assert len(vm.estado.items) == 1


def test_cargar_emite_empty_sin_datos() -> None:
    vm = PacientesViewModel(lambda _activo, _texto: [])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.EMPTY]
    assert vm.estado.items == []


def test_cargar_emite_error_si_falla() -> None:
    def _rompe(_activo: bool, _texto: str) -> list[PacienteRowFake]:
        raise RuntimeError("boom")

    vm = PacientesViewModel(_rompe)
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.ERROR]
    assert vm.estado.error_key == "ux_states.pacientes.error"


def test_aplicar_filtro_normaliza_espacios_y_actualiza_last_search_safe() -> None:
    vm = PacientesViewModel(lambda _activo, texto: [PacienteRowFake(id=1, nombre=texto)])

    vm.aplicar_filtro("  Ana  ")

    assert vm.estado.filtro_texto == "Ana"
    assert vm.estado.last_search_safe == "Ana"
    assert vm.estado.items[0].nombre == "Ana"


def test_seleccionar_actualiza_id_seleccionado() -> None:
    vm = PacientesViewModel(lambda _activo, _texto: [])

    vm.seleccionar(33)

    assert vm.estado.seleccion_id == 33


def test_refrescar_emite_toast_ok_y_error() -> None:
    eventos_ok: list[str] = []
    vm_ok = PacientesViewModel(lambda _activo, _texto: [PacienteRowFake(id=4, nombre="L")])
    vm_ok.subscribe_eventos(lambda evento: eventos_ok.append(str(evento.payload.get("key"))))

    vm_ok.refrescar()

    assert "toast.refresh_ok_pacientes" in eventos_ok

    eventos_fail: list[str] = []
    vm_fail = PacientesViewModel(lambda _activo, _texto: 1 / 0)
    vm_fail.subscribe_eventos(lambda evento: eventos_fail.append(str(evento.payload.get("key"))))

    vm_fail.refrescar()

    assert "toast.refresh_fail" in eventos_fail


def test_aplicar_filtro_acepta_none_y_no_rompe() -> None:
    vm = PacientesViewModel(lambda _activo, texto: [PacienteRowFake(id=10, nombre=texto)])

    vm.aplicar_filtro(None)

    assert vm.estado.filtro_texto == ""
    assert vm.estado.last_search_safe is None
    assert vm.estado.items[0].nombre == ""


def test_actualizar_contexto_normaliza_none_sin_excepcion() -> None:
    vm = PacientesViewModel(lambda _activo, _texto: [])

    vm.actualizar_contexto(activo=True, texto=None, seleccion_id=5)

    assert vm.estado.filtro_texto == ""
    assert vm.estado.last_search_safe is None
    assert vm.estado.seleccion_id == 5

from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.ui.viewmodels.auditoria_viewmodel import AuditoriaViewModel
from clinicdesk.app.ui.viewmodels.contratos import EstadoPantalla


@dataclass(slots=True)
class AuditoriaRowFake:
    entidad_id: int


def test_cargar_transicion_loading_content() -> None:
    vm = AuditoriaViewModel(lambda _texto: [AuditoriaRowFake(entidad_id=1)])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.CONTENT]


def test_cargar_transicion_loading_empty() -> None:
    vm = AuditoriaViewModel(lambda _texto: [])
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.EMPTY]


def test_cargar_transicion_loading_error() -> None:
    vm = AuditoriaViewModel(lambda _texto: 1 / 0)
    estados: list[EstadoPantalla] = []
    vm.subscribe(lambda estado: estados.append(estado.estado_pantalla))

    vm.cargar()

    assert estados == [EstadoPantalla.LOADING, EstadoPantalla.ERROR]
    assert vm.estado.error_key == "ux_states.auditoria.error"


def test_aplicar_filtro_normaliza_espacios() -> None:
    vm = AuditoriaViewModel(lambda texto: [AuditoriaRowFake(entidad_id=len(texto))])

    vm.aplicar_filtro("  admin  ")

    assert vm.estado.filtro_texto == "admin"
    assert vm.estado.last_search_safe == "admin"


def test_refrescar_emite_toasts_ok_empty_fail() -> None:
    eventos_ok: list[str] = []
    vm_ok = AuditoriaViewModel(lambda _texto: [AuditoriaRowFake(entidad_id=2)])
    vm_ok.subscribe_eventos(lambda evento: eventos_ok.append(str(evento.payload.get("key"))))
    vm_ok.refrescar()
    assert eventos_ok == ["toast.refresh_ok_auditoria"]

    eventos_empty: list[str] = []
    vm_empty = AuditoriaViewModel(lambda _texto: [])
    vm_empty.subscribe_eventos(lambda evento: eventos_empty.append(str(evento.payload.get("key"))))
    vm_empty.refrescar()
    assert eventos_empty == ["toast.refresh_empty_auditoria", "toast.refresh_ok_auditoria"]

    eventos_fail: list[str] = []
    vm_fail = AuditoriaViewModel(lambda _texto: 1 / 0)
    vm_fail.subscribe_eventos(lambda evento: eventos_fail.append(str(evento.payload.get("key"))))
    vm_fail.refrescar()
    assert eventos_fail == ["toast.refresh_fail"]


def test_exportar_csv_emite_evento_job() -> None:
    vm = AuditoriaViewModel(lambda _texto: [])
    eventos: list[tuple[str, object]] = []
    vm.subscribe_eventos(lambda evento: eventos.append((evento.tipo, evento.payload.get("accion"))))

    vm.exportar_csv()

    assert eventos == [("job", "exportar_auditoria_csv")]

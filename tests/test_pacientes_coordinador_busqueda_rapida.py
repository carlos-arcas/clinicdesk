from __future__ import annotations

from clinicdesk.app.pages.pacientes.coordinadores.busqueda_rapida import CoordinadorBusquedaRapidaPacientes
from clinicdesk.app.pages.pacientes.coordinadores.contexto_operativo import CoordinadorContextoPacientes


class _ThreadFalso:
    def __init__(self, running: bool) -> None:
        self._running = running

    def isRunning(self) -> bool:
        return self._running


def test_busqueda_rapida_descarta_resultado_obsoleto_por_contexto() -> None:
    contexto = CoordinadorContextoPacientes()
    contexto.on_show()
    coordinador = CoordinadorBusquedaRapidaPacientes(contexto=contexto)
    consumidos: list[list[object]] = []
    token = coordinador.preparar(consumidos.append)

    assert token is not None

    contexto.on_hide()

    assert coordinador.consumir_resultado({"rows": [1, 2]}, token) is False
    assert consumidos == []


def test_busqueda_rapida_entrega_rows_y_bloquea_nuevo_arranque_si_sigue_corriendo() -> None:
    contexto = CoordinadorContextoPacientes()
    contexto.on_show()
    coordinador = CoordinadorBusquedaRapidaPacientes(contexto=contexto)
    consumidos: list[list[object]] = []

    token = coordinador.preparar(consumidos.append)

    assert token is not None

    coordinador.registrar_thread(thread=_ThreadFalso(True), worker=None, relay=None)
    assert coordinador.preparar(consumidos.append) is None

    coordinador.finalizar_thread()
    assert coordinador.consumir_resultado({"rows": ["ok"]}, token) is True
    assert consumidos == [["ok"]]

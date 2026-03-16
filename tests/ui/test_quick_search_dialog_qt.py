from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtCore import Qt
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.preferencias.preferencias_usuario import (
    PreferenciasRepository,
    PreferenciasService,
    PreferenciasUsuario,
)
from clinicdesk.app.i18n import I18nManager

try:
    from clinicdesk.app.ui.quick_search_debounce import DespachadorDebounce
    from clinicdesk.app.ui.widgets.quick_search_dialog import ContextoBusquedaRapida, QuickSearchDialog
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"Dependencias Qt no disponibles: {exc}", allow_module_level=True)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


class RepositorioPreferenciasMemoria(PreferenciasRepository):
    def __init__(self) -> None:
        self._preferencias = PreferenciasUsuario()

    def get(self, perfil_id: str | None) -> PreferenciasUsuario:
        del perfil_id
        return self._preferencias

    def set(self, perfil_id: str | None, preferencias: PreferenciasUsuario) -> None:
        del perfil_id
        self._preferencias = preferencias


def _crear_contexto(selecciones: list[str], consultas: list[str]) -> ContextoBusquedaRapida[str]:
    resultados = ["paciente_a", "paciente_b"]

    def _buscar_async(texto: str, resolver) -> None:
        consultas.append(texto)
        resolver(resultados)

    return ContextoBusquedaRapida(
        contexto_id="pacientes",
        titulo_key="quick_search.pacientes.title",
        placeholder_key="quick_search.placeholder",
        empty_key="quick_search.empty",
        buscar_async=_buscar_async,
        on_select=selecciones.append,
        render_item=lambda valor: f"item:{valor}",
    )


def _crear_dialogo() -> QuickSearchDialog:
    preferencias_service = PreferenciasService(RepositorioPreferenciasMemoria())
    dialogo = QuickSearchDialog(I18nManager("es"), preferencias_service)
    dialogo._debounce = DespachadorDebounce(delay_ms=0)
    return dialogo


def test_quick_search_dialog_open_enter_y_escape(qtbot) -> None:
    selecciones: list[str] = []
    consultas: list[str] = []
    dialogo = _crear_dialogo()
    qtbot.addWidget(dialogo)
    contexto = _crear_contexto(selecciones, consultas)

    dialogo.open_for(contexto)
    assert dialogo.windowTitle() == dialogo._i18n.t(contexto.titulo_key)

    qtbot.keyClicks(dialogo._input, "ana")
    qtbot.waitUntil(lambda: dialogo._lista.count() == 2)
    assert consultas[-1] == "ana"

    qtbot.keyClick(dialogo._input, Qt.Key_Return)
    qtbot.waitUntil(lambda: not dialogo.isVisible())
    assert selecciones == ["paciente_a"]

    dialogo.open_for(contexto)
    assert dialogo.isVisible()
    qtbot.keyClick(dialogo, Qt.Key_Escape)
    qtbot.waitUntil(lambda: not dialogo.isVisible())


def _crear_contexto_controlado(selecciones: list[str]):
    callbacks: list[object] = []

    def _buscar_async(texto: str, resolver) -> None:
        del texto
        callbacks.append(resolver)

    contexto = ContextoBusquedaRapida(
        contexto_id="pacientes",
        titulo_key="quick_search.pacientes.title",
        placeholder_key="quick_search.placeholder",
        empty_key="quick_search.empty",
        buscar_async=_buscar_async,
        on_select=selecciones.append,
        render_item=lambda valor: f"item:{valor}",
    )
    return contexto, callbacks


def test_quick_search_descarta_resultado_con_token_obsoleto(qtbot) -> None:
    selecciones: list[str] = []
    dialogo = _crear_dialogo()
    qtbot.addWidget(dialogo)
    contexto, callbacks = _crear_contexto_controlado(selecciones)
    dialogo.open_for(contexto)

    qtbot.keyClicks(dialogo._input, "ana")
    qtbot.waitUntil(lambda: len(callbacks) == 1)
    primer_callback = callbacks[0]

    dialogo._input.clear()
    qtbot.keyClicks(dialogo._input, "anabel")
    qtbot.waitUntil(lambda: len(callbacks) == 2)

    primer_callback(["obsoleto"])
    qtbot.wait(20)
    assert dialogo._lista.count() == 0


def test_quick_search_no_renderiza_si_dialogo_ya_cerro(qtbot) -> None:
    selecciones: list[str] = []
    dialogo = _crear_dialogo()
    qtbot.addWidget(dialogo)
    contexto, callbacks = _crear_contexto_controlado(selecciones)
    dialogo.open_for(contexto)

    qtbot.keyClicks(dialogo._input, "ana")
    qtbot.waitUntil(lambda: len(callbacks) == 1)
    dialogo.close()
    qtbot.waitUntil(lambda: not dialogo.isVisible())

    callbacks[0](["paciente_tardio"])
    qtbot.wait(20)
    assert dialogo._lista.count() == 0


def test_quick_search_respuestas_fuera_de_orden_conserva_ultima_busqueda(qtbot) -> None:
    selecciones: list[str] = []
    dialogo = _crear_dialogo()
    qtbot.addWidget(dialogo)
    contexto, callbacks = _crear_contexto_controlado(selecciones)
    dialogo.open_for(contexto)

    qtbot.keyClicks(dialogo._input, "a")
    qtbot.waitUntil(lambda: len(callbacks) == 1)
    primero = callbacks[0]

    qtbot.keyClicks(dialogo._input, "na")
    qtbot.waitUntil(lambda: len(callbacks) == 2)
    segundo = callbacks[1]

    segundo(["vigente_1", "vigente_2"])
    qtbot.waitUntil(lambda: dialogo._lista.count() == 2)
    primero(["obsoleto"])
    qtbot.wait(20)

    assert dialogo._lista.count() == 2
    assert dialogo._lista.item(0).text() == "item:vigente_1"


def test_quick_search_renderiza_y_selecciona_cuando_respuesta_es_vigente(qtbot) -> None:
    selecciones: list[str] = []
    dialogo = _crear_dialogo()
    qtbot.addWidget(dialogo)
    contexto, callbacks = _crear_contexto_controlado(selecciones)
    dialogo.open_for(contexto)

    qtbot.keyClicks(dialogo._input, "ana")
    qtbot.waitUntil(lambda: len(callbacks) == 1)
    callbacks[0](["paciente_ok"])
    qtbot.waitUntil(lambda: dialogo._lista.count() == 1)

    qtbot.keyClick(dialogo._input, Qt.Key_Return)
    qtbot.waitUntil(lambda: not dialogo.isVisible())
    assert selecciones == ["paciente_ok"]

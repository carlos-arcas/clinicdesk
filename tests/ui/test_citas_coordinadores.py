from __future__ import annotations

from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.pages.citas.coordinadores.coordinador_intents_citas import CoordinadorIntentsCitas
from clinicdesk.app.pages.citas.coordinadores.coordinador_refresh_citas import CoordinadorRefreshCitas


def _intent_base() -> CitasNavigationIntentDTO:
    return CitasNavigationIntentDTO(cita_id_destino=15)


def test_coordinador_refresh_descarta_token_obsoleto_e_invisible() -> None:
    coordinador = CoordinadorRefreshCitas()

    token_vigente = coordinador.solicitar_token()
    assert token_vigente == 1
    assert coordinador.es_vigente(1)

    token_prev = coordinador.invalidar_vigente()
    assert token_prev == 1
    assert not coordinador.es_vigente(1)

    token_hide = coordinador.desactivar_pagina()
    assert token_hide == 2
    assert coordinador.solicitar_token() is None
    assert not coordinador.pagina_visible()


def test_coordinador_intents_aplica_vigente_y_descarta_obsoleto() -> None:
    coordinador = CoordinadorIntentsCitas()
    intent = _intent_base()
    coordinador.registrar_intent(intent)

    vigente = coordinador.resolver_para_vista("LISTA", "LISTA")
    assert vigente.intent == intent
    assert not vigente.obsoleto

    coordinador.registrar_intent(_intent_base())
    coordinador.invalidar_intents()
    obsoleto = coordinador.resolver_para_vista("LISTA", "LISTA")
    assert obsoleto.intent is None
    assert not obsoleto.obsoleto


def test_coordinador_intents_omite_vista_inactiva() -> None:
    coordinador = CoordinadorIntentsCitas()
    coordinador.registrar_intent(_intent_base())

    estado = coordinador.resolver_para_vista("CALENDARIO", "LISTA")
    assert estado.intent is None
    assert not estado.obsoleto

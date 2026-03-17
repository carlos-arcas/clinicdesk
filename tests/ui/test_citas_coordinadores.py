from __future__ import annotations

from clinicdesk.app.application.citas import FiltrosCitasDTO
from clinicdesk.app.application.citas.navigation_intent import CitasNavigationIntentDTO
from clinicdesk.app.pages.citas.coordinadores.coordinador_banners_citas import CoordinadorBannersCitas
from clinicdesk.app.pages.citas.coordinadores.coordinador_intents_citas import CoordinadorIntentsCitas
from clinicdesk.app.pages.citas.coordinadores.coordinador_refresh_citas import CoordinadorRefreshCitas
from clinicdesk.app.pages.citas.coordinadores.coordinador_salud_prediccion_citas import CoordinadorSaludPrediccionCitas


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


def test_coordinador_banners_activa_y_desactiva_estado_auxiliar() -> None:
    coordinador = CoordinadorBannersCitas()
    filtros_previos = FiltrosCitasDTO(rango_preset="HOY")

    coordinador.activar_filtro_calidad("SIN_CHECKIN", filtros_previos)
    assert coordinador.hay_filtro_calidad_activo()
    assert coordinador.filtro_calidad_activo() == "SIN_CHECKIN"
    assert coordinador.filtros_previos_o(FiltrosCitasDTO(rango_preset="SEMANA")) == filtros_previos

    coordinador.desactivar_filtro_calidad()
    assert not coordinador.hay_filtro_calidad_activo()
    assert coordinador.filtros_previos_o(FiltrosCitasDTO(rango_preset="SEMANA")).rango_preset == "SEMANA"


def test_coordinador_salud_prediccion_actualiza_estado_y_logueo_por_token() -> None:
    coordinador = CoordinadorSaludPrediccionCitas()
    token = coordinador.registrar_nuevo_refresh()
    assert token == 1

    duracion, espera = coordinador.actualizar_estimaciones(True, lambda _: ({1: "ALTO"}, {1: "MEDIO"}))
    assert duracion[1] == "ALTO"
    assert espera[1] == "MEDIO"
    assert coordinador.tipos_estimacion_disponibles(1) == ["duracion", "espera"]

    estado = coordinador.estado_aviso_salud(True, "ROJO", "VERDE")
    assert estado.mostrar
    assert coordinador.debe_loguear_aviso(estado.mostrar)
    coordinador.marcar_aviso_logueado()
    assert not coordinador.debe_loguear_aviso(estado.mostrar)

    coordinador.registrar_nuevo_refresh()
    assert coordinador.debe_loguear_aviso(True)
    assert coordinador.nivel_estimacion(999, "duracion") == "NO_DISPONIBLE"

from __future__ import annotations

from clinicdesk.app.pages.pacientes.coordinadores.contexto_operativo import CoordinadorContextoPacientes


def test_contexto_invalida_tokens_al_ocultar() -> None:
    coordinador = CoordinadorContextoPacientes()
    coordinador.on_show()
    token_carga = coordinador.nuevo_token_carga()
    token_busqueda = coordinador.nueva_busqueda_rapida()

    assert coordinador.puede_consumir_carga(token_carga) is True
    assert coordinador.puede_consumir_busqueda_rapida(token_busqueda) is True

    coordinador.on_hide()

    assert coordinador.pagina_visible is False
    assert coordinador.puede_consumir_carga(token_carga) is False
    assert coordinador.puede_consumir_busqueda_rapida(token_busqueda) is False


def test_refresh_diferido_solo_se_consume_en_contexto_vigente() -> None:
    coordinador = CoordinadorContextoPacientes()
    token = coordinador.on_show()

    assert coordinador.programar_refresh_on_show(token) is True
    assert coordinador.consumir_refresh_programado() is True

    token_obsoleto = coordinador.on_show()
    assert coordinador.programar_refresh_on_show(token_obsoleto) is True
    coordinador.on_show()

    assert coordinador.consumir_refresh_programado() is False

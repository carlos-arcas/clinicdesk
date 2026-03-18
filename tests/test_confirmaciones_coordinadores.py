from __future__ import annotations

from clinicdesk.app.pages.confirmaciones.coordinadores.contexto_operativo import (
    CoordinadorContextoConfirmaciones,
)
from clinicdesk.app.pages.confirmaciones.coordinadores.refresh_operativo import (
    CoordinadorRefreshOperativoConfirmaciones,
)


def test_contexto_invalida_whatsapp_al_ocultar() -> None:
    coordinador = CoordinadorContextoConfirmaciones()
    coordinador.on_show()
    operation_id = coordinador.nueva_operacion_whatsapp_rapido()

    assert coordinador.es_whatsapp_rapido_vigente(operation_id) is True

    coordinador.on_hide()

    assert coordinador.es_contexto_operativo_vigente() is False
    assert coordinador.es_whatsapp_rapido_vigente(operation_id) is False


def test_contexto_descarta_tokens_obsoletos_y_pagina_no_visible() -> None:
    coordinador = CoordinadorContextoConfirmaciones()
    coordinador.on_show()
    token_vigente = coordinador.nuevo_token_carga()
    coordinador.nuevo_token_carga()

    assert coordinador.puede_consumir_carga(token_vigente) is False

    coordinador.on_hide()

    assert coordinador.puede_consumir_carga(coordinador.token_carga) is False


def test_refresh_operativo_solo_ocurre_en_contexto_vigente() -> None:
    coordinador = CoordinadorContextoConfirmaciones()
    refrescos: list[bool] = []
    refresh = CoordinadorRefreshOperativoConfirmaciones(
        contexto=coordinador,
        on_refresh=refrescos.append,
    )

    coordinador.on_show()
    operation_id = coordinador.nueva_operacion_whatsapp_rapido()

    assert refresh.solicitar_desde_whatsapp(origen="whatsapp_rapido_ok", operation_id=operation_id) is True
    assert refrescos == [False]
    assert refresh.token_refresh_operativo == 1

    coordinador.on_hide()

    assert refresh.solicitar_desde_whatsapp(origen="whatsapp_rapido_fail", operation_id=operation_id) is False
    assert refresh.solicitar_desde_lote(operation_id) is False
    assert refrescos == [False]

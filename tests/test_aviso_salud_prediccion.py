from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import (
    CacheSaludPrediccionPorRefresh,
    debe_mostrar_aviso_salud_prediccion,
)


def test_debe_mostrar_aviso_salud_prediccion_con_riesgo_desactivado() -> None:
    assert debe_mostrar_aviso_salud_prediccion(False, "ROJO") is False


def test_debe_mostrar_aviso_salud_prediccion_en_verde() -> None:
    assert debe_mostrar_aviso_salud_prediccion(True, "VERDE") is False


def test_debe_mostrar_aviso_salud_prediccion_en_amarillo_y_rojo() -> None:
    assert debe_mostrar_aviso_salud_prediccion(True, "AMARILLO") is True
    assert debe_mostrar_aviso_salud_prediccion(True, "ROJO") is True


def test_cache_salud_prediccion_llama_una_vez_por_refresh() -> None:
    llamadas = 0

    def fake_obtener_salud() -> dict[str, str]:
        nonlocal llamadas
        llamadas += 1
        return {"estado": "AMARILLO"}

    cache = CacheSaludPrediccionPorRefresh(fake_obtener_salud)

    primera = cache.obtener(token_refresh=1)
    segunda = cache.obtener(token_refresh=1)
    tercera = cache.obtener(token_refresh=2)

    assert primera == {"estado": "AMARILLO"}
    assert segunda == {"estado": "AMARILLO"}
    assert tercera == {"estado": "AMARILLO"}
    assert llamadas == 2

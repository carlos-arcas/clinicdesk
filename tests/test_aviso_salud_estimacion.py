from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.aviso_salud_prediccion import CacheSaludPrediccionPorRefresh
from clinicdesk.app.application.prediccion_operativa.ux_estimaciones import (
    debe_mostrar_aviso_salud_estimacion,
    mensaje_no_disponible_estimacion,
)


def test_mensaje_no_disponible_estimacion_devuelve_clave_i18n() -> None:
    assert mensaje_no_disponible_estimacion("duracion") == "estimaciones.no_disponible"
    assert mensaje_no_disponible_estimacion("espera") == "estimaciones.no_disponible"


def test_debe_mostrar_aviso_salud_estimacion_toggle_off() -> None:
    assert debe_mostrar_aviso_salud_estimacion(False, "ROJO") is False


def test_debe_mostrar_aviso_salud_estimacion_estados() -> None:
    assert debe_mostrar_aviso_salud_estimacion(True, "VERDE") is False
    assert debe_mostrar_aviso_salud_estimacion(True, "AMARILLO") is True
    assert debe_mostrar_aviso_salud_estimacion(True, "ROJO") is True


def test_cache_estimaciones_llama_una_vez_por_refresh() -> None:
    llamadas = 0

    def fake_obtener_estimaciones() -> tuple[dict[int, str], dict[int, str]]:
        nonlocal llamadas
        llamadas += 1
        return ({1: "BAJO"}, {1: "MEDIO"})

    cache = CacheSaludPrediccionPorRefresh(fake_obtener_estimaciones)

    primera = cache.obtener(token_refresh=1)
    segunda = cache.obtener(token_refresh=1)
    tercera = cache.obtener(token_refresh=2)

    assert primera == ({1: "BAJO"}, {1: "MEDIO"})
    assert segunda == ({1: "BAJO"}, {1: "MEDIO"})
    assert tercera == ({1: "BAJO"}, {1: "MEDIO"})
    assert llamadas == 2

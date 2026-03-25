from __future__ import annotations

from types import SimpleNamespace

import pytest

try:
    from clinicdesk.app.pages.prediccion_ausencias.page import PagePrediccionAusencias
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)


def _page_minima() -> PagePrediccionAusencias:
    return object.__new__(PagePrediccionAusencias)


def test_on_entrenar_click_no_duplica_arranque_si_running() -> None:
    page = _page_minima()
    page._entrenamiento_activo = True
    page._datos_aptos = True
    page._set_estado_error = lambda _reason: None
    page._iniciar_entrenamiento_premium = lambda: (_ for _ in ()).throw(AssertionError("no debe iniciar"))

    page._on_entrenar_click()


def test_on_entrenar_ok_refresca_componentes_clave() -> None:
    page = _page_minima()
    llamadas: list[str] = []
    page._set_estado_success = lambda: llamadas.append("estado_ok")
    page._limpiar_recordatorio_por_entrenamiento = lambda: llamadas.append("recordatorio")
    page._actualizar_salud = lambda: llamadas.append("salud")
    page._actualizar_resultados_recientes = lambda: llamadas.append("resultados")
    page._cargar_previsualizacion = lambda: llamadas.append("preview")
    page._registrar_telemetria = lambda _evento, _resultado: llamadas.append("telemetria")
    page._set_estado_error = lambda _reason: llamadas.append("estado_error")

    page._on_entrenar_ok(SimpleNamespace(citas_usadas=12, fecha_entrenamiento="2026-03-25"))

    assert llamadas == ["estado_ok", "recordatorio", "salud", "resultados", "preview", "telemetria"]


def test_on_entrenar_fail_normaliza_reason_code() -> None:
    page = _page_minima()
    llamados: list[tuple[str, str]] = []
    page._set_estado_error = lambda reason: llamados.append(("estado", reason))
    page._escribir_incidente_fallo = lambda **kwargs: llamados.append(("incidente", kwargs["reason_code"]))
    page._registrar_telemetria = lambda _evento, _resultado: llamados.append(("telemetria", "fail"))

    page._on_entrenar_fail("dataset_empty")

    assert ("estado", "dataset_empty") in llamados
    assert ("incidente", "dataset_empty") in llamados

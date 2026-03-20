from __future__ import annotations

import os
from datetime import datetime

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from clinicdesk.app.i18n import I18nManager
    from clinicdesk.app.pages.gestion.page import PageGestionDashboard
    from clinicdesk.app.pages.prediccion_operativa.page import PagePrediccionOperativa
    from clinicdesk.app.ui.main_window import MainWindow
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)
from tests.support.ruta_critica_desktop import (
    crear_cita_programada,
    obtener_fecha_base_prediccion,
    seed_historial_y_agenda_prediccion,
)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


def _fila_vigilancia_por_hora(page: PageGestionDashboard, hora: str) -> int:
    for fila in range(page.tabla_vigilancia.rowCount()):
        item = page.tabla_vigilancia.item(fila, 0)
        if item is not None and item.text() == hora:
            return fila
    return -1


def _abrir_pagina(window: MainWindow, key: str, tipo_esperado: type[object]) -> object:
    widget = window.navigate(key)
    assert widget is not None
    assert isinstance(widget, tipo_esperado)
    return widget


def _esperar_entrenamiento(qtbot, page: PagePrediccionOperativa, tipo: str, cita_id: int) -> None:
    bloque = page._bloque(tipo)
    qtbot.mouseClick(bloque.btn_preparar, Qt.LeftButton)
    qtbot.waitUntil(lambda: bloque.progress.isVisible())
    qtbot.waitUntil(lambda: not bloque.progress.isVisible())
    qtbot.waitUntil(lambda: page._background_entrenamiento.tiene_hilos_activos() is False)
    qtbot.waitUntil(lambda: page._predicciones_duracion.get(cita_id) is not None)
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.msg.listo")


def test_ml_desktop_propaga_estado_cross_modulo_hacia_gestion_y_limpia_background_al_salir(
    qtbot,
    container,
    seed_data,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLINICDESK_PREFS_PATH", (tmp_path / "prefs_cross_module.json").as_posix())
    fecha_base = obtener_fecha_base_prediccion()
    seed_historial_y_agenda_prediccion(container, seed_data, ahora=fecha_base)
    cita_hoy_id = crear_cita_programada(
        container,
        seed_data,
        datetime(2026, 4, 15, 17, 0, 0),
        motivo="Agenda hoy ML cross-module",
    )
    container.connection.commit()

    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)
    qtbot.addWidget(window)
    window.show()

    page_gestion = _abrir_pagina(window, "gestion", PageGestionDashboard)
    qtbot.waitUntil(lambda: page_gestion._estado_labels[1].text() != "-")

    assert page_gestion._estado_labels[1].text() == page_gestion._i18n.t("dashboard_gestion.salud.label.no_disponible")
    assert page_gestion._estado_labels[2].text() == page_gestion._i18n.t("dashboard_gestion.salud.label.no_disponible")
    assert container.prediccion_operativa_facade.obtener_estimaciones_agenda() == ({}, {})
    assert _fila_vigilancia_por_hora(page_gestion, "17:00") == -1

    page_ml = _abrir_pagina(window, "prediccion_operativa", PagePrediccionOperativa)
    page_ml.chk_mostrar_agenda.setChecked(True)
    _esperar_entrenamiento(qtbot, page_ml, "duracion", cita_hoy_id)

    duraciones, esperas = container.prediccion_operativa_facade.obtener_estimaciones_agenda()
    assert page_ml._predicciones_duracion[cita_hoy_id] == duraciones[cita_hoy_id]
    assert esperas == {}

    page_gestion = _abrir_pagina(window, "gestion", PageGestionDashboard)
    qtbot.waitUntil(
        lambda: page_gestion._estado_labels[1].text()
        in {
            page_gestion._i18n.t("dashboard_gestion.salud.label.verde"),
            page_gestion._i18n.t("dashboard_gestion.salud.label.amarillo"),
        }
    )
    qtbot.waitUntil(lambda: _fila_vigilancia_por_hora(page_gestion, "17:00") != -1)

    fila = _fila_vigilancia_por_hora(page_gestion, "17:00")
    assert fila >= 0
    assert page_gestion.tabla_vigilancia.item(fila, 3).text() == page_gestion._i18n.t(
        "dashboard_gestion.citas_vigilar.senal.duracion"
    )
    assert page_gestion._estado_labels[2].text() == page_gestion._i18n.t("dashboard_gestion.salud.label.no_disponible")
    assert duraciones[cita_hoy_id] == "ALTO"

    page_ml = _abrir_pagina(window, "prediccion_operativa", PagePrediccionOperativa)
    bloque_espera = page_ml._bloque("espera")
    qtbot.mouseClick(bloque_espera.btn_preparar, Qt.LeftButton)
    qtbot.waitUntil(lambda: bloque_espera.progress.isVisible())

    page_gestion = _abrir_pagina(window, "gestion", PageGestionDashboard)
    assert page_ml._runs_entrenamiento.run_vigente("espera", 1) is False
    qtbot.waitUntil(lambda: page_ml._background_entrenamiento.tiene_hilos_activos() is False)

    page_gestion._cargar_dashboard()
    qtbot.waitUntil(
        lambda: page_gestion._estado_labels[2].text()
        in {
            page_gestion._i18n.t("dashboard_gestion.salud.label.verde"),
            page_gestion._i18n.t("dashboard_gestion.salud.label.amarillo"),
        }
    )
    duraciones, esperas = container.prediccion_operativa_facade.obtener_estimaciones_agenda()
    fila = _fila_vigilancia_por_hora(page_gestion, "17:00")
    assert fila >= 0
    assert page_gestion.tabla_vigilancia.item(fila, 3).text() == " · ".join(
        [
            page_gestion._i18n.t("dashboard_gestion.citas_vigilar.senal.duracion"),
            page_gestion._i18n.t("dashboard_gestion.citas_vigilar.senal.espera"),
        ]
    )
    assert page_ml._predicciones_espera[cita_hoy_id] == esperas[cita_hoy_id]
    assert esperas[cita_hoy_id] == "ALTO"

    window.close()
    qtbot.waitUntil(lambda: page_ml._background_entrenamiento.tiene_hilos_activos() is False)
    assert not window.isVisible()

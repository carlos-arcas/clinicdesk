from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.prediccion_operativa.page import PagePrediccionOperativa
from tests.support.ruta_critica_desktop import obtener_fecha_base_prediccion, seed_historial_y_agenda_prediccion


class _TelemetriaSpy:
    def __init__(self) -> None:
        self.eventos: list[dict[str, object]] = []

    def ejecutar(self, **kwargs) -> None:
        self.eventos.append(kwargs)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _crear_page(
    container, *, contexto_usuario: UserContext, telemetria: _TelemetriaSpy | None = None
) -> PagePrediccionOperativa:
    _app()
    return PagePrediccionOperativa(
        facade=container.prediccion_operativa_facade,
        i18n=I18nManager("es"),
        telemetria_uc=telemetria or _TelemetriaSpy(),
        contexto_usuario=contexto_usuario,
        autorizador_acciones=container.autorizador_acciones,
    )


def _entrenamiento_inline(**kwargs) -> None:
    resultado = kwargs["ejecutar"]()
    run = kwargs["run"]
    kwargs["on_ok"](run.tipo, run.token, resultado)
    kwargs["on_thread_finished"](run.tipo, run.token)


def test_usuario_autorizado_puede_entrenar(qtbot, container, seed_data, monkeypatch: pytest.MonkeyPatch) -> None:
    cita_id = seed_historial_y_agenda_prediccion(container, seed_data, ahora=obtener_fecha_base_prediccion())
    telemetria = _TelemetriaSpy()
    page = _crear_page(
        container, contexto_usuario=UserContext(role=Role.ADMIN, username="admin"), telemetria=telemetria
    )
    qtbot.addWidget(page)
    page.chk_mostrar_agenda.setChecked(True)
    page.on_show()
    monkeypatch.setattr(page._background_entrenamiento, "iniciar_entrenamiento", _entrenamiento_inline)

    page._entrenar("duracion")

    qtbot.waitUntil(lambda: page._predicciones_duracion.get(cita_id) is not None)
    bloque = page._bloque("duracion")
    assert bloque.btn_preparar.isEnabled() is True
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.msg.listo")
    assert any(
        evento["contexto"] == "page=prediccion_operativa;resultado=click_duracion" for evento in telemetria.eventos
    )
    assert any(evento["contexto"] == "page=prediccion_operativa;resultado=ok_duracion" for evento in telemetria.eventos)


def test_usuario_sin_permisos_no_puede_entrenar_y_ve_feedback_controlado(
    qtbot, container, seed_data, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_historial_y_agenda_prediccion(container, seed_data, ahora=obtener_fecha_base_prediccion())
    telemetria = _TelemetriaSpy()
    page = _crear_page(
        container, contexto_usuario=UserContext(role=Role.READONLY, username="readonly"), telemetria=telemetria
    )
    qtbot.addWidget(page)
    page.on_show()
    bloque = page._bloque("duracion")
    llamadas: list[object] = []
    monkeypatch.setattr(
        page._background_entrenamiento, "iniciar_entrenamiento", lambda **kwargs: llamadas.append(kwargs)
    )

    assert bloque.btn_preparar.isEnabled() is False
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.seguridad.sin_permiso_entrenar")

    page._entrenar("duracion")

    assert llamadas == []
    assert bloque.progress.isVisible() is False
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.seguridad.sin_permiso_entrenar")
    assert telemetria.eventos[-1]["contexto"] == "page=prediccion_operativa;resultado=denegado_duracion"


def test_reintento_tambien_queda_bloqueado_para_usuario_sin_permiso(
    qtbot, container, seed_data, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_historial_y_agenda_prediccion(container, seed_data, ahora=obtener_fecha_base_prediccion())
    telemetria = _TelemetriaSpy()
    page = _crear_page(
        container, contexto_usuario=UserContext(role=Role.READONLY, username="readonly"), telemetria=telemetria
    )
    qtbot.addWidget(page)
    page.on_show()
    bloque = page._bloque("espera")
    bloque.btn_reintentar.setVisible(True)
    llamadas: list[object] = []
    monkeypatch.setattr(
        page._background_entrenamiento, "iniciar_entrenamiento", lambda **kwargs: llamadas.append(kwargs)
    )

    page._entrenar("espera")

    assert llamadas == []
    assert bloque.btn_reintentar.isEnabled() is False
    assert bloque.btn_reintentar.isVisible() is True
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.seguridad.sin_permiso_entrenar")
    assert telemetria.eventos[-1]["contexto"] == "page=prediccion_operativa;resultado=denegado_espera"


def test_usuario_lectura_puede_ver_explicacion_sin_entrenar_nuevo(qtbot, container, seed_data, monkeypatch) -> None:
    cita_id = seed_historial_y_agenda_prediccion(container, seed_data, ahora=obtener_fecha_base_prediccion())
    page_admin = _crear_page(container, contexto_usuario=UserContext(role=Role.ADMIN, username="admin"))
    qtbot.addWidget(page_admin)
    page_admin.chk_mostrar_agenda.setChecked(True)
    page_admin.on_show()
    monkeypatch.setattr(page_admin._background_entrenamiento, "iniciar_entrenamiento", _entrenamiento_inline)
    page_admin._entrenar("duracion")
    qtbot.waitUntil(lambda: page_admin._predicciones_duracion.get(cita_id) is not None)
    nivel = page_admin._predicciones_duracion[cita_id]

    telemetria = _TelemetriaSpy()
    page = _crear_page(
        container, contexto_usuario=UserContext(role=Role.READONLY, username="readonly"), telemetria=telemetria
    )
    qtbot.addWidget(page)
    page.chk_mostrar_agenda.setChecked(True)
    page.on_show()

    page._mostrar_por_que("duracion", cita_id, nivel)

    qtbot.waitUntil(lambda: isinstance(page._dialogo_explicacion_activo, QMessageBox))
    dialogo = page._dialogo_explicacion_activo
    assert dialogo is not None
    assert dialogo.text()
    assert "readonly" not in dialogo.text().lower()
    assert telemetria.eventos[-1]["entidad_id"] == cita_id
    assert "Paciente" not in (telemetria.eventos[-1]["contexto"] or "")
    dialogo.accept()
    qtbot.waitUntil(lambda: page._dialogo_explicacion_activo is None)

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QPushButton
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app import main as app_main
from clinicdesk.app.main import ContextoEntrypointDesktop, ControlEntrypointDesktop
from clinicdesk.app.security.auth import AuthService
from clinicdesk.app.ui.login_dialog import LoginOutcome
from clinicdesk.app.ui.main_window import MainWindow
from tests.conftest import TEST_DB_PATH
from tests.support.ruta_critica_desktop import obtener_fecha_base_prediccion, seed_historial_y_agenda_prediccion

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


class DialogoLoginAceptado:
    def __init__(self, username: str = "admin") -> None:
        self.outcome = LoginOutcome(demo_mode=False, username=username)

    def exec(self) -> int:
        return QDialog.Accepted


@dataclass(slots=True)
class ResultadoEscenarioEntrypoint:
    futura_id: int
    ventana: MainWindow | None = None
    pagina_ml: object | None = None
    dialogo_explicacion_abierto: bool = False
    error: Exception | None = None
    finalizado: bool = False


class EscenarioEntrypointDesktopControlado:
    def __init__(self, resultado: ResultadoEscenarioEntrypoint) -> None:
        self._resultado = resultado
        self._contexto: ContextoEntrypointDesktop | None = None

    def preparar(self, contexto: ContextoEntrypointDesktop) -> None:
        self._contexto = contexto
        QTimer.singleShot(0, self._esperar_ventana_principal)

    def _esperar_ventana_principal(self) -> None:
        assert self._contexto is not None
        ventana = self._contexto.ventana_principal
        if not isinstance(ventana, MainWindow) or not ventana.isVisible():
            QTimer.singleShot(10, self._esperar_ventana_principal)
            return
        self._resultado.ventana = ventana
        self._ir_a_prediccion_operativa()

    def _ir_a_prediccion_operativa(self) -> None:
        assert self._resultado.ventana is not None
        ventana = self._resultado.ventana
        try:
            item_gestion = ventana._sidebar_item_by_key["gestion"]
            ventana.sidebar.setCurrentRow(ventana.sidebar.row(item_gestion))
            pagina_gestion = ventana.stack.currentWidget()
            if pagina_gestion is None:
                QTimer.singleShot(10, self._ir_a_prediccion_operativa)
                return
            QTest.mouseClick(pagina_gestion.btn_ir_estimaciones_duracion, Qt.LeftButton)
            QTimer.singleShot(0, self._esperar_pagina_ml)
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _esperar_pagina_ml(self) -> None:
        assert self._resultado.ventana is not None
        try:
            pagina = self._resultado.ventana.stack.currentWidget()
            if pagina is None or pagina.__class__.__name__ != "PagePrediccionOperativa":
                QTimer.singleShot(10, self._esperar_pagina_ml)
                return
            self._resultado.pagina_ml = pagina
            pagina.chk_mostrar_agenda.setChecked(True)
            bloque = pagina._bloque("duracion")
            QTest.mouseClick(bloque.btn_preparar, Qt.LeftButton)
            QTimer.singleShot(0, self._esperar_feedback_entrenamiento)
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _esperar_feedback_entrenamiento(self) -> None:
        pagina = self._resultado.pagina_ml
        if pagina is None:
            self._abortar(AssertionError("La página ML no quedó registrada"))
            return
        try:
            bloque = pagina._bloque("duracion")
            if bloque.progress.isVisible():
                QTimer.singleShot(10, self._esperar_resultado_entrenamiento)
                return
            QTimer.singleShot(10, self._esperar_feedback_entrenamiento)
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _esperar_resultado_entrenamiento(self) -> None:
        pagina = self._resultado.pagina_ml
        if pagina is None:
            self._abortar(AssertionError("La página ML no quedó registrada"))
            return
        try:
            bloque = pagina._bloque("duracion")
            if pagina._predicciones_duracion.get(self._resultado.futura_id) is None or bloque.progress.isVisible():
                QTimer.singleShot(10, self._esperar_resultado_entrenamiento)
                return
            assert bloque.lbl_feedback.text() == pagina._i18n.t("prediccion_operativa.msg.listo")
            assert bloque.tabla.rowCount() >= 1
            boton = bloque.tabla.cellWidget(0, 5)
            assert isinstance(boton, QPushButton)
            QTest.mouseClick(boton, Qt.LeftButton)
            QTimer.singleShot(0, self._esperar_dialogo_explicacion)
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _esperar_dialogo_explicacion(self) -> None:
        pagina = self._resultado.pagina_ml
        if pagina is None:
            self._abortar(AssertionError("La página ML no quedó registrada"))
            return
        try:
            dialogo = pagina._dialogo_explicacion_activo
            if not isinstance(dialogo, QMessageBox):
                QTimer.singleShot(10, self._esperar_dialogo_explicacion)
                return
            self._resultado.dialogo_explicacion_abierto = True
            assert dialogo.text()
            dialogo.accept()
            QTimer.singleShot(0, self._cerrar_loop)
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _cerrar_loop(self) -> None:
        pagina = self._resultado.pagina_ml
        if pagina is None:
            self._abortar(AssertionError("La página ML no quedó registrada"))
            return
        try:
            if pagina._dialogo_explicacion_activo is not None:
                QTimer.singleShot(10, self._cerrar_loop)
                return
            assert pagina._background_entrenamiento.tiene_hilos_activos() is False
            self._resultado.finalizado = True
            assert self._contexto is not None
            self._contexto.app.quit()
        except Exception as exc:  # noqa: BLE001
            self._abortar(exc)

    def _abortar(self, exc: Exception) -> None:
        self._resultado.error = exc
        assert self._contexto is not None
        self._contexto.app.quit()


def test_main_entrypoint_e2e_controlado_arranca_navega_ml_y_cierra_limpio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    db_connection,
    container,
    seed_data,
) -> None:
    AuthService(db_connection).create_user("admin", "secret123")
    cita_futura_id = seed_historial_y_agenda_prediccion(
        container,
        seed_data,
        ahora=obtener_fecha_base_prediccion(),
    )
    db_connection.commit()
    monkeypatch.setenv("CLINICDESK_DB_PATH", TEST_DB_PATH.as_posix())
    monkeypatch.setenv("CLINICDESK_PREFS_PATH", (tmp_path / "user_prefs.json").as_posix())
    monkeypatch.setattr(app_main, "instalar_hooks_crash", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "configure_logging", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "install_global_exception_hook", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "_install_ui_log_buffer", lambda: None)
    monkeypatch.setattr(app_main, "load_qss", lambda: "")

    resultado = ResultadoEscenarioEntrypoint(futura_id=cita_futura_id)
    escenario = EscenarioEntrypointDesktopControlado(resultado)
    control = ControlEntrypointDesktop(
        crear_dialogo_login=lambda *_args, **_kwargs: DialogoLoginAceptado(),
        preparar_loop=escenario.preparar,
    )

    codigo = app_main.main(control)

    assert codigo == 0
    assert resultado.error is None, repr(resultado.error)
    assert resultado.finalizado is True
    assert isinstance(resultado.ventana, MainWindow)
    assert resultado.dialogo_explicacion_abierto is True
    assert resultado.pagina_ml is not None
    assert resultado.pagina_ml._predicciones_duracion.get(cita_futura_id) in {"BAJO", "MEDIO", "ALTO"}
    app = QApplication.instance()
    assert app is not None
    assert all(not widget.isVisible() for widget in app.topLevelWidgets())

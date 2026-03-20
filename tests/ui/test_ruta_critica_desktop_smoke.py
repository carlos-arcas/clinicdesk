from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QDate, Qt
    from PySide6.QtWidgets import QDialog
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.citas import FiltrosCitasDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app import main as app_main
from clinicdesk.app.pages.citas.page import PageCitas
from clinicdesk.app.pages.prediccion_operativa.page import PagePrediccionOperativa
from tests.support.ruta_critica_desktop import FECHA_BASE_CITAS, seed_historial_y_agenda_prediccion

pytestmark = [pytest.mark.ui, pytest.mark.uiqt, pytest.mark.integration]


@dataclass(slots=True)
class _FakeDialogoCita:
    datos: object

    def exec(self) -> int:
        return QDialog.Accepted

    def get_data(self) -> object:
        return self.datos


class _TelemetriaDummy:
    def ejecutar(self, **_kwargs) -> None:
        return None


def _filtros_dia(fecha: datetime) -> FiltrosCitasDTO:
    return FiltrosCitasDTO(
        rango_preset="PERSONALIZADO",
        desde=fecha.replace(hour=0, minute=0, second=0, microsecond=0),
        hasta=fecha.replace(hour=23, minute=59, second=59, microsecond=0),
    )


def test_smoke_arranque_controlado_pyside(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_main, "instalar_hooks_crash", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "configure_logging", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "install_global_exception_hook", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app_main, "_install_ui_log_buffer", lambda: None)
    monkeypatch.setattr(app_main, "load_qss", lambda: "")

    app, run_id = app_main._inicializar_app()

    assert run_id
    assert app is not None
    app.quit()


def test_smoke_desktop_citas_crear_y_consultar(qtbot, container, seed_data, monkeypatch: pytest.MonkeyPatch) -> None:
    page = PageCitas(container, I18nManager("es"))
    qtbot.addWidget(page)

    fecha_base = FECHA_BASE_CITAS
    page.calendar.setSelectedDate(QDate(2024, 5, 20))
    page._filtros_aplicados = _filtros_dia(fecha_base)
    page._refrescar_vistas_principales("test_setup")
    qtbot.waitUntil(lambda: page.table_lista.rowCount() == 0)

    from clinicdesk.app.controllers import citas_controller as citas_controller_module
    from clinicdesk.app.pages.citas.dialogs.dialog_cita_form import CitaFormData

    monkeypatch.setattr(
        citas_controller_module,
        "CitaFormDialog",
        lambda *args, **kwargs: _FakeDialogoCita(
            CitaFormData(
                paciente_id=seed_data["paciente_activo_id"],
                medico_id=seed_data["medico_activo_id"],
                sala_id=seed_data["sala_activa_id"],
                inicio="2024-05-20 09:00:00",
                fin="2024-05-20 09:30:00",
                motivo="Control anual",
                observaciones="Creada desde smoke desktop",
            )
        ),
    )

    page._on_new()

    qtbot.waitUntil(lambda: page.table_lista.rowCount() == 1)
    assert page.lbl_estado.text() == ""
    assert page.table_lista.item(0, 0).data(Qt.UserRole) == page._citas_lista_ids[0]
    textos_fila = [
        page.table_lista.item(0, columna).text()
        for columna in range(page.table_lista.columnCount())
        if page.table_lista.item(0, columna) is not None
    ]
    assert any("Laura" in texto for texto in textos_fila)


def test_smoke_desktop_prediccion_operativa_entrena_y_previsualiza(qtbot, container, seed_data, monkeypatch) -> None:
    cita_futura_id = seed_historial_y_agenda_prediccion(container, seed_data)
    page = PagePrediccionOperativa(
        facade=container.prediccion_operativa_facade,
        i18n=I18nManager("es"),
        telemetria_uc=_TelemetriaDummy(),
        contexto_usuario=container.user_context,
    )
    qtbot.addWidget(page)
    page.on_show()

    bloque = page._bloque("duracion")
    assert "60" in bloque.lbl_datos.text()

    def _entrenamiento_inline(**kwargs) -> None:
        resultado = kwargs["ejecutar"]()
        run = kwargs["run"]
        kwargs["on_ok"](run.tipo, run.token, resultado)
        kwargs["on_thread_finished"](run.tipo, run.token)

    monkeypatch.setattr(page._background_entrenamiento, "iniciar_entrenamiento", _entrenamiento_inline)

    page._entrenar("duracion")

    qtbot.waitUntil(lambda: not bloque.progress.isVisible())
    qtbot.waitUntil(lambda: page._predicciones_duracion.get(cita_futura_id) is not None)
    assert bloque.lbl_feedback.text() == page._i18n.t("prediccion_operativa.msg.listo")
    assert page._predicciones_duracion[cita_futura_id] in {"BAJO", "MEDIO", "ALTO"}
    assert bloque.tabla.rowCount() >= 1
    assert bloque.tabla.item(0, 0).text()


def test_smoke_desktop_prediccion_operativa_muestra_explicacion_util(qtbot, container, seed_data, monkeypatch) -> None:
    cita_futura_id = seed_historial_y_agenda_prediccion(container, seed_data)
    page = PagePrediccionOperativa(
        facade=container.prediccion_operativa_facade,
        i18n=I18nManager("es"),
        telemetria_uc=_TelemetriaDummy(),
        contexto_usuario=container.user_context,
    )
    qtbot.addWidget(page)
    page.chk_mostrar_agenda.setChecked(True)
    page.on_show()

    def _entrenamiento_inline(**kwargs) -> None:
        resultado = kwargs["ejecutar"]()
        run = kwargs["run"]
        kwargs["on_ok"](run.tipo, run.token, resultado)
        kwargs["on_thread_finished"](run.tipo, run.token)

    capturado: dict[str, str] = {}

    def _capturar_explicacion(_parent, titulo: str, texto: str) -> None:
        capturado["titulo"] = titulo
        capturado["texto"] = texto

    monkeypatch.setattr(page._background_entrenamiento, "iniciar_entrenamiento", _entrenamiento_inline)
    monkeypatch.setattr("clinicdesk.app.pages.prediccion_operativa.page.QMessageBox.information", _capturar_explicacion)

    page._entrenar("duracion")
    qtbot.waitUntil(lambda: page._predicciones_duracion.get(cita_futura_id) is not None)
    page._mostrar_por_que("duracion", cita_futura_id, page._predicciones_duracion[cita_futura_id])

    assert capturado["titulo"] == page._i18n.t("prediccion_operativa.btn.ver_por_que")
    assert capturado["texto"]
    assert "•" in capturado["texto"]

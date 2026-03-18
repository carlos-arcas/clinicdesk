from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.security import UserContext
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.prediccion_operativa.page import PagePrediccionOperativa


class _TelemetriaDummy:
    def ejecutar(self, **_kwargs) -> None:
        return None


RUTA_PREDICCION = Path("clinicdesk/app/pages/prediccion_operativa/page.py")


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _page(container) -> PagePrediccionOperativa:
    return PagePrediccionOperativa(
        facade=container.prediccion_operativa_facade,
        i18n=I18nManager("es"),
        telemetria_uc=_TelemetriaDummy(),
        contexto_usuario=UserContext(username="tester", roles=("admin",), demo_mode=True),
    )


def _metodo_prediccion(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_PREDICCION.read_text(encoding="utf-8"))
    clase = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePrediccionOperativa"
    )
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_on_train_ok_descarta_token_obsoleto(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = _page(container)
    page._contexto_operativo.on_show()
    page._runs_entrenamiento.iniciar_run("duracion", page._contexto_operativo.token_contexto)
    page._runs_entrenamiento.iniciar_run("duracion", page._contexto_operativo.token_contexto)
    monkeypatch.setattr(page, "_comprobar_datos", lambda _tipo: pytest.fail("no debe refrescar token obsoleto"))

    page._on_train_ok("duracion", 1, object())


def test_on_train_fail_omite_ui_si_contexto_ya_no_visible(container) -> None:
    _app()
    page = _page(container)
    page._contexto_operativo.on_show()
    run = page._runs_entrenamiento.iniciar_run("espera", page._contexto_operativo.token_contexto)
    bloque = page._bloque("espera")
    bloque.progress.setVisible(True)

    page.on_hide()
    page._on_train_fail("espera", run.token, object())

    assert bloque.progress.isVisible() is True


def test_on_hide_invalida_runs_activos(container) -> None:
    _app()
    page = _page(container)
    page._contexto_operativo.on_show()
    run = page._runs_entrenamiento.iniciar_run("duracion", page._contexto_operativo.token_contexto)

    page.on_hide()

    assert page._runs_entrenamiento.run_vigente("duracion", run.token) is False


def test_puede_consumir_resultado_solo_si_run_y_contexto_siguen_vigentes(container) -> None:
    _app()
    page = _page(container)
    token_contexto = page._contexto_operativo.on_show()
    run = page._runs_entrenamiento.iniciar_run("duracion", token_contexto)

    assert page._puede_consumir_resultado_entrenamiento("duracion", run.token) is True

    page._contexto_operativo.on_show()

    assert page._puede_consumir_resultado_entrenamiento("duracion", run.token) is False


def test_entrenar_delega_background_con_token_y_contexto_vigente(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = _page(container)
    token_contexto = page._contexto_operativo.on_show()
    llamado: dict[str, object] = {}

    def _fake_iniciar_entrenamiento(**kwargs) -> None:
        llamado.update(kwargs)

    monkeypatch.setattr(page._background_entrenamiento, "iniciar_entrenamiento", _fake_iniciar_entrenamiento)

    page._entrenar("duracion")

    run = llamado["run"]
    assert run.tipo == "duracion"
    assert run.token == 1
    assert run.token_contexto == token_contexto
    assert callable(llamado["ejecutar"])


def test_page_se_apoya_en_coordinadores_para_estado_async() -> None:
    metodo = _metodo_prediccion("__init__")
    nombres = {
        node.attr
        for node in ast.walk(metodo)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self"
    }

    assert "_contexto_operativo" in nombres
    assert "_runs_entrenamiento" in nombres
    assert "_background_entrenamiento" in nombres


def test_iniciar_entrenamiento_background_no_usa_qthread_directo_en_page() -> None:
    metodo = _metodo_prediccion("_iniciar_entrenamiento_background")
    nombres = {node.id for node in ast.walk(metodo) if isinstance(node, ast.Name)}

    assert "QThread" not in nombres

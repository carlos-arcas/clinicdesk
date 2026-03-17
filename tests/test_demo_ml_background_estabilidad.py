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

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.demo_ml.page import PageDemoML

RUTA_PAGE = Path("clinicdesk/app/pages/demo_ml/page.py")


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _metodo(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_PAGE.read_text(encoding="utf-8"))
    clase = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PageDemoML")
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_run_background_no_conecta_callback_arbitrario_directo() -> None:
    metodo = _metodo("_run_background")
    directas = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "finished"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "on_done"
    ]
    assert directas == []


def test_background_resultado_run_obsoleta_no_pisa_run_actual(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = PageDemoML(container.demo_ml_facade, I18nManager("es"))
    page._run_id = "run-nueva"
    monkeypatch.setattr(page, "isVisible", lambda: True)

    llamado = {"score": False}
    monkeypatch.setattr(page, "_on_score_done", lambda _payload: llamado.__setitem__("score", True))

    page._on_background_done("run-vieja", "score", object())

    assert llamado["score"] is False


def test_workflow_progress_no_toca_dialogo_si_ya_cerrado(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = PageDemoML(container.demo_ml_facade, I18nManager("es"))
    page._run_id = "run-activa"
    monkeypatch.setattr(page, "isVisible", lambda: True)
    page.progress_dialog = None

    page._on_workflow_progress("run-activa", 50, "mitad")

    assert page.progress_dialog is None

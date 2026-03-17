from __future__ import annotations

import os

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


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _page(container) -> PagePrediccionOperativa:
    return PagePrediccionOperativa(
        facade=container.prediccion_operativa_facade,
        i18n=I18nManager("es"),
        telemetria_uc=_TelemetriaDummy(),
        contexto_usuario=UserContext(username="tester", roles=("admin",), demo_mode=True),
    )


def test_on_train_ok_descarta_token_obsoleto(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = _page(container)
    page._token_entrenamiento["duracion"] = 3
    monkeypatch.setattr(page, "isVisible", lambda: True)

    llamado = {"ok": False}
    monkeypatch.setattr(page, "_comprobar_datos", lambda _tipo: llamado.__setitem__("ok", True))

    page._on_train_ok("duracion", 2, object())

    assert llamado["ok"] is False


def test_on_train_fail_omite_ui_si_no_visible(container, monkeypatch: pytest.MonkeyPatch) -> None:
    _app()
    page = _page(container)
    page._token_entrenamiento["espera"] = 1
    monkeypatch.setattr(page, "isVisible", lambda: False)

    bloque = page._bloque("espera")
    bloque.progress.setVisible(True)

    page._on_train_fail("espera", 1, object())

    assert bloque.progress.isVisible() is True


import ast
from pathlib import Path

RUTA_PREDICCION = Path("clinicdesk/app/pages/prediccion_operativa/page.py")


def _metodo_prediccion(nombre: str) -> ast.FunctionDef:
    tree = ast.parse(RUTA_PREDICCION.read_text(encoding="utf-8"))
    clase = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagePrediccionOperativa"
    )
    return next(node for node in clase.body if isinstance(node, ast.FunctionDef) and node.name == nombre)


def test_ejecutar_worker_conecta_relay_y_slots_sin_lambdas_fragiles() -> None:
    metodo = _metodo_prediccion("_ejecutar_worker")
    lambda_connects = [
        node
        for node in ast.walk(metodo)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
        and node.args
        and isinstance(node.args[0], ast.Lambda)
    ]
    assert lambda_connects == []

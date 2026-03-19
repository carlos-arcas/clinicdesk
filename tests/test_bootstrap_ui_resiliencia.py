from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication, QLabel, QStackedWidget
except ImportError:  # pragma: no cover
    QApplication = None
    QLabel = None
    QStackedWidget = None

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui import bootstrap_ui


@dataclass(frozen=True)
class _PaginaStub:
    key: str
    title: str
    factory: object


def _app() -> QApplication:
    if QApplication is None:  # pragma: no cover
        pytest.skip("PySide6 no disponible")
    return QApplication.instance() or QApplication([])


def test_get_pages_devuelve_placeholder_si_falla_import(monkeypatch, caplog) -> None:
    registry_specs = (
        bootstrap_ui.RegistroPaginaSpec("ok", "mod.ok"),
        bootstrap_ui.RegistroPaginaSpec("rota", "mod.rota"),
    )

    def _register_ok(registry, _container) -> None:
        registry.register(_PaginaStub(key="ok", title="OK", factory=lambda: None))

    def _cargar_registrador(spec):
        if spec.page_id == "rota":
            raise ImportError("módulo no disponible")
        return _register_ok

    monkeypatch.setattr(bootstrap_ui, "_cargar_registrador", _cargar_registrador)

    caplog.set_level(logging.ERROR)
    pages = bootstrap_ui.get_pages(container=object(), i18n=I18nManager("es"), specs_paginas=registry_specs)

    assert [page.key for page in pages] == ["ok", "rota"]
    rota = next(page for page in pages if page.key == "rota")
    assert rota.title == "rota"
    assert callable(rota.factory)
    assert any(record.msg == "page_register_fail" for record in caplog.records)


@pytest.mark.ui
@pytest.mark.uiqt
def test_placeholder_recupera_pagina_real_tras_retry(monkeypatch) -> None:
    _app()
    estado = {"disponible": False}
    spec = bootstrap_ui.RegistroPaginaSpec("rota", "mod.rota")

    def _register_pagina(registry, _container) -> None:
        if not estado["disponible"]:
            raise RuntimeError("registro caído")
        registry.register(_PaginaStub(key="rota", title="Rota", factory=lambda: QLabel("Página real")))

    monkeypatch.setattr(bootstrap_ui, "_cargar_registrador", lambda _spec: _register_pagina)
    pages = bootstrap_ui.get_pages(container=object(), i18n=I18nManager("es"), specs_paginas=(spec,))

    stack = QStackedWidget()
    placeholder = pages[0].factory()
    stack.addWidget(placeholder)
    stack.setCurrentWidget(placeholder)

    estado["disponible"] = True
    placeholder._reintentar_carga()

    actual = stack.currentWidget()
    assert actual is not placeholder
    assert isinstance(actual, QLabel)
    assert actual.text() == "Página real"

    nueva_instancia = pages[0].factory()
    assert isinstance(nueva_instancia, QLabel)
    assert nueva_instancia.text() == "Página real"


@pytest.mark.ui
@pytest.mark.uiqt
def test_placeholder_permanece_si_retry_sigue_fallando(monkeypatch) -> None:
    _app()
    spec = bootstrap_ui.RegistroPaginaSpec("rota", "mod.rota")

    def _register_pagina(_registry, _container) -> None:
        raise RuntimeError("todavía roto")

    monkeypatch.setattr(bootstrap_ui, "_cargar_registrador", lambda _spec: _register_pagina)
    pages = bootstrap_ui.get_pages(container=object(), i18n=I18nManager("es"), specs_paginas=(spec,))

    stack = QStackedWidget()
    placeholder = pages[0].factory()
    stack.addWidget(placeholder)
    stack.setCurrentWidget(placeholder)

    placeholder._reintentar_carga()

    assert stack.currentWidget() is placeholder
    assert "Todavía no se puede cargar" in placeholder._feedback.text()
    assert "todavía roto" in placeholder._feedback.text()


def test_bootstrap_construye_paginas_validas_sin_afectar_flujo_normal(monkeypatch) -> None:
    specs = (
        bootstrap_ui.RegistroPaginaSpec("ok", "mod.ok"),
        bootstrap_ui.RegistroPaginaSpec("otra", "mod.otra"),
    )

    def _cargar_registrador(spec):
        def _register_ok(registry, _container) -> None:
            registry.register(
                _PaginaStub(key=spec.page_id, title=spec.page_id.upper(), factory=lambda: {"page": spec.page_id})
            )

        return _register_ok

    monkeypatch.setattr(bootstrap_ui, "_cargar_registrador", _cargar_registrador)
    pages = bootstrap_ui.get_pages(container=object(), i18n=I18nManager("es"), specs_paginas=specs)

    assert [page.key for page in pages] == ["ok", "otra"]
    assert [page.title for page in pages] == ["OK", "OTRA"]
    assert [page.factory() for page in pages] == [{"page": "ok"}, {"page": "otra"}]

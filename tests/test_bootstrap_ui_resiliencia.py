from __future__ import annotations

import logging
from dataclasses import dataclass

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui import bootstrap_ui


@dataclass(frozen=True)
class _PaginaStub:
    key: str
    title: str
    factory: object


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

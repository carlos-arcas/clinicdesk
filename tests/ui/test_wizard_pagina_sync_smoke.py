from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover - depende del sistema
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.ui.wizard_bienvenida.paginas.pagina_sync import PaginaSync


class _I18nFake:
    def t(self, key: str) -> str:
        return key


@pytest.fixture(scope="session")
def qapp() -> Iterator[QApplication]:
    app = QApplication.instance() or QApplication([])
    yield app


def test_pagina_sync_smoke_crea_boton_guia(qapp: QApplication) -> None:
    del qapp
    pagina = PaginaSync(i18n=_I18nFake(), on_abrir_guia=lambda: None)

    assert hasattr(pagina, "_boton_ver_guia")

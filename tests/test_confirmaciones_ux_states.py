from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.confirmaciones.dtos import ResultadoConfirmacionesDTO
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.confirmaciones.page import PageConfirmaciones


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_confirmaciones_muestra_empty_si_no_hay_items(container) -> None:
    _app()
    page = PageConfirmaciones(container, I18nManager("es"))

    def _arrancar_falso(*, token: int) -> None:
        page._on_carga_ok(ResultadoConfirmacionesDTO(total=0, mostrados=0, items=[], salud_prediccion=None), token)

    page._arrancar_worker_carga = _arrancar_falso  # type: ignore[method-assign]
    page._load_data(reset=True)

    assert page._estado_pantalla.estado_actual == "empty"

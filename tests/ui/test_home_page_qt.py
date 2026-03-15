from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from clinicdesk.app.pages.gestion.page import PageGestionDashboard
    from clinicdesk.app.pages.home.page import PageHome
    from clinicdesk.app.i18n import I18nManager
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

pytestmark = [pytest.mark.ui, pytest.mark.uiqt]


def test_home_reutiliza_dashboard_gestion(container, qtbot) -> None:
    home = PageHome(container=container, i18n=I18nManager("es"))
    qtbot.addWidget(home)

    dashboard = home.findChild(PageGestionDashboard)

    assert dashboard is not None


def test_home_on_show_delega_en_dashboard(container, qtbot, monkeypatch) -> None:
    home = PageHome(container=container, i18n=I18nManager("es"))
    qtbot.addWidget(home)
    llamadas = {"total": 0}

    def _fake_on_show() -> None:
        llamadas["total"] += 1

    monkeypatch.setattr(home._page_gestion, "on_show", _fake_on_show)

    home.on_show()

    assert llamadas["total"] == 1

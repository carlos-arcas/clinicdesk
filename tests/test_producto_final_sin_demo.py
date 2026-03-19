from __future__ import annotations

import os
from pathlib import Path

import pytest

from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.ui import bootstrap_ui

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from clinicdesk.app.ui.main_window import MainWindow
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)


def test_bootstrap_producto_final_no_registra_demo() -> None:
    specs = bootstrap_ui._build_specs_por_defecto()

    assert all(spec.page_id != "demo_ml" for spec in specs)
    assert all("demo_ml" not in spec.modulo_registro for spec in specs)


def test_main_window_no_expone_accion_seed_demo(container) -> None:
    window = MainWindow(container, I18nManager("es"), on_logout=lambda: None)

    assert not hasattr(window, "action_seed_demo_reset")
    assert "demo_ml" not in window._factory_by_key
    assert "demo_ml" not in window._sidebar_item_by_key


def test_residuos_demo_eliminados_del_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    assert not (repo_root / "clinicdesk" / "app" / "pages" / "demo_ml").exists()
    assert not (repo_root / "scripts" / "run_demo.py").exists()


def test_container_expone_nombre_analitico_y_compatibilidad_legacy(container) -> None:
    assert hasattr(container, "analitica_ml_facade")
    assert container.analitica_ml_facade is container.demo_ml_facade


def test_docs_principales_no_presentan_api_como_demo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    rutas = [
        repo_root / "README.md",
        repo_root / "docs" / "minimizacion_salidas.md",
        repo_root / "docs" / "features.md",
        repo_root / "docs" / "features_pendientes.md",
    ]

    for ruta in rutas:
        contenido = ruta.read_text(encoding="utf-8")
        assert "API demo" not in contenido

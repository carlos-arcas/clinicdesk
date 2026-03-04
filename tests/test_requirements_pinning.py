from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components.requirements_pinning import (
    check_requirements_pinneados,
    linea_requerimiento_pinneada,
)


def test_linea_requerimiento_pinneada_acepta_pin_exacto() -> None:
    assert linea_requerimiento_pinneada("pytest==8.3.2")
    assert linea_requerimiento_pinneada("# comentario")


def test_linea_requerimiento_pinneada_rechaza_rango() -> None:
    assert not linea_requerimiento_pinneada("PySide6>=6.8,<6.11")


def test_check_requirements_pinneados_falla_con_lineas_no_pinneadas(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("cryptography>=46\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\npytest==8.3.2\n", encoding="utf-8")

    assert check_requirements_pinneados(repo_root=tmp_path) == 9


def test_check_requirements_pinneados_pasa_con_archivos_pinneados(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("cryptography==46.0.5\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\npytest==8.3.2\n", encoding="utf-8")

    assert check_requirements_pinneados(repo_root=tmp_path) == 0

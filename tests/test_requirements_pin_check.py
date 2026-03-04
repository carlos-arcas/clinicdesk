from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_components import requirements_pin_check


def test_linea_esta_pinneada_acepta_formato_valido() -> None:
    assert requirements_pin_check.linea_esta_pinneada("pytest==8.3.2")
    assert requirements_pin_check.linea_esta_pinneada("  # comentario")
    assert requirements_pin_check.linea_esta_pinneada("-r requirements.txt")


def test_validar_requirements_pinneados_detecta_rangos(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "pytest==8.3.2\nruff>=0.8\ncryptography<47\n",
        encoding="utf-8",
    )

    errores = requirements_pin_check.validar_requirements_pinneados(requirements)

    assert errores == [(2, "ruff>=0.8"), (3, "cryptography<47")]


def test_check_requirements_pinneados_falla_si_hay_linea_no_pinneada(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("pytest==8.3.2\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff>=0.8\n", encoding="utf-8")

    assert requirements_pin_check.check_requirements_pinneados(repo_root=tmp_path) == 9

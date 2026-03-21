from __future__ import annotations

from pathlib import Path
import pytest

from scripts.quality_gate_components import entorno_python
from scripts.quality_gate_components.toolchain import InterpreteEsperado


@pytest.fixture
def interprete_esperado(tmp_path: Path) -> InterpreteEsperado:
    return InterpreteEsperado(
        version_minima="3.11",
        python_repo=tmp_path / ".venv" / "bin" / "python",
        comando_activar=f"source {tmp_path / '.venv' / 'bin' / 'activate'}",
        comando_recrear=f"rm -rf {tmp_path / '.venv'} && python scripts/setup.py",
    )


def test_diagnosticar_interprete_detecta_fuera_de_venv(monkeypatch: pytest.MonkeyPatch, interprete_esperado: InterpreteEsperado) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.setattr(entorno_python.sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(entorno_python.sys, "prefix", "/usr")
    monkeypatch.setattr(entorno_python.sys, "base_prefix", "/usr")

    estado = entorno_python.diagnosticar_interprete(interprete_esperado)

    assert estado.venv_activo is False
    assert estado.usa_python_repo is False
    assert "fuera del venv del repo" in estado.detalle


def test_diagnosticar_interprete_detecta_python_incompatible(
    monkeypatch: pytest.MonkeyPatch, interprete_esperado: InterpreteEsperado
) -> None:
    monkeypatch.setattr(entorno_python.sys, "version_info", type("_VersionInfo", (), {"major": 3, "minor": 10, "micro": 9, "__ge__": lambda self, other: (3, 10, 9) >= other})())
    monkeypatch.setattr(entorno_python.sys, "executable", "/usr/bin/python3.10")
    monkeypatch.setattr(entorno_python.sys, "prefix", "/usr")
    monkeypatch.setattr(entorno_python.sys, "base_prefix", "/usr")
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    estado = entorno_python.diagnosticar_interprete(interprete_esperado)

    assert estado.version_compatible is False
    assert ">= 3.11" in estado.detalle
    assert "python scripts/setup.py" in estado.detalle

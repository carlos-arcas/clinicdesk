from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.quality_gate_components import ruff_checks


def test_run_required_ruff_checks_falla_si_falta_configuracion(tmp_path: Path) -> None:
    resultado = ruff_checks.run_required_ruff_checks(tmp_path)
    assert resultado == 1


def test_run_required_ruff_checks_invoca_ruff_con_targets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    comandos: list[list[str]] = []

    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py", "tests/b.py"])

    class Resultado:
        returncode = 0
        stdout = "ruff 0.12.0"
        stderr = ""

    def fake_run(command, **kwargs):
        comandos.append(command)
        return Resultado()

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 0
    assert comandos == [
        [sys.executable, "-m", "ruff", "--version"],
        [sys.executable, "-m", "ruff", "check", "scripts/a.py", "tests/b.py"],
        [sys.executable, "-m", "ruff", "format", "--check", "scripts/a.py", "tests/b.py"],
    ]

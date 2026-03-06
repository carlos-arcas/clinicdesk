from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.quality_gate_components import ruff_checks


class _Resultado:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_required_ruff_checks_falla_si_falta_configuracion(tmp_path: Path) -> None:
    resultado = ruff_checks.run_required_ruff_checks(tmp_path)
    assert resultado == 1


def test_run_required_ruff_checks_invoca_ruff_con_targets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    comandos: list[list[str]] = []

    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py", "tests/b.py"])

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        return _Resultado(returncode=0, stdout="ruff 0.12.0")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 0
    assert comandos == [
        [sys.executable, "-m", "ruff", "--version"],
        [sys.executable, "-m", "ruff", "check", "scripts/a.py", "tests/b.py"],
        [sys.executable, "-m", "ruff", "format", "--check", "scripts/a.py", "tests/b.py"],
    ]


def test_run_required_ruff_checks_retorna_error_si_falla_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    comandos: list[list[str]] = []

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        return _Resultado(returncode=2, stderr="fallo")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 2
    assert comandos == [[sys.executable, "-m", "ruff", "--version"]]


def test_genera_diff_y_artefacto_si_format_check_falla(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])
    comandos: list[list[str]] = []

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=0, stdout="--- diff ---", stderr="")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert comandos[-1] == [
        sys.executable,
        "-m",
        "ruff",
        "format",
        "--diff",
        "tests/test_checklist_funcional_contract.py",
        "tests/test_quality_thresholds_contract.py",
    ]
    artefacto = (tmp_path / "docs" / "ruff_format_diff.txt").read_text(encoding="utf-8")
    assert "--- diff ---" in artefacto
    assert "returncode: 0" in artefacto


def test_persistencia_estable_si_diff_falla(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=2, stdout="", stderr="diff-error")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    artefacto = (tmp_path / "docs" / "ruff_format_diff.txt").read_text(encoding="utf-8")
    assert "returncode: 2" in artefacto
    assert "diff-error" in artefacto


def test_persistencia_estable_si_diff_no_se_puede_ejecutar(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            raise OSError("sin ejecutable")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    artefacto = (tmp_path / "docs" / "ruff_format_diff.txt").read_text(encoding="utf-8")
    assert "returncode: no-ejecutado" in artefacto
    assert "sin ejecutable" in artefacto

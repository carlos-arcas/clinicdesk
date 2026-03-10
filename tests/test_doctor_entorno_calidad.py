from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.quality_gate_components import doctor_entorno_calidad_core as doctor


class _Resultado:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_doctor_entorno_alineado(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text(
        "ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n",
        encoding="utf-8",
    )

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.8.4")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        if command[2] == "pip_audit":
            return _Resultado(0, stdout="pip-audit 2.7.3")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    assert doctor.codigo_salida_estable(diagnostico) == 0


def test_doctor_reporta_ruff_ausente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n", encoding="utf-8")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(1, stderr="No module named ruff")
        return _Resultado(0, stdout="ok 1.0.0")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    assert doctor.codigo_salida_estable(diagnostico) == 2


def test_doctor_reporta_ruff_version_incorrecta(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n", encoding="utf-8")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.14.11")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        if command[2] == "pip_audit":
            return _Resultado(0, stdout="pip-audit 2.7.3")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    assert doctor.codigo_salida_estable(diagnostico) == 3
    lineas = doctor.renderizar_reporte(diagnostico)
    assert any("versión desalineada" in linea for linea in lineas)


def test_doctor_detecta_wheelhouse_requerido_ausente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n", encoding="utf-8")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.8.4")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        if command[2] == "pip_audit":
            return _Resultado(0, stdout="pip-audit 2.7.3")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path, wheelhouse=tmp_path / "wheelhouse")
    assert doctor.codigo_salida_estable(diagnostico, exigir_wheelhouse=True) == 4

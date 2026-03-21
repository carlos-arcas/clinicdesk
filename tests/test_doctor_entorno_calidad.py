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


def _escribir_lock_dev(tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.in").write_text("ruff\npytest\nmypy\npip-audit\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(
        "ruff==0.8.4\npytest==8.3.2\nmypy==1.13.0\npip-audit==2.7.3\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text('[tool.mypy]\npython_version = "3.11"\n', encoding="utf-8")


def test_doctor_entorno_alineado(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

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
    assert diagnostico.source_of_truth.startswith("requirements-dev.txt")
    assert Path(diagnostico.python_path) == Path(sys.executable).resolve()


def test_doctor_reporta_herramienta_faltante_con_comando_accionable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(1, stderr="No module named ruff")
        return _Resultado(0, stdout="ok 1.0.0")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    assert doctor.codigo_salida_estable(diagnostico) == 2
    lineas = doctor.renderizar_reporte(diagnostico)
    assert any("ruff: falta en el entorno; gate bloqueado" in linea for linea in lineas)
    assert any("python -m pip install -r requirements-dev.txt" in linea for linea in lineas)


def test_doctor_reporta_ruff_version_incorrecta(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

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
    assert any("versión desalineada; gate bloqueado" in linea for linea in lineas)
    assert any("esperada=0.8.4; instalada=0.14.11" in linea for linea in lineas)


def test_doctor_detecta_lock_dev_incompleto(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.3.2\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[tool.mypy]\npython_version = "3.11"\n', encoding="utf-8")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        raise AssertionError(f"No debería ejecutar herramientas cuando el lock es inválido: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    assert doctor.codigo_salida_estable(diagnostico) == 5
    assert diagnostico.toolchain_error is not None
    assert "ruff" in diagnostico.toolchain_error


def test_doctor_detecta_wheelhouse_requerido_ausente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

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
    lineas = doctor.renderizar_reporte(diagnostico, exigir_wheelhouse=True)
    assert any("Modo offline requerido" in linea for linea in lineas)


def test_doctor_usa_metadata_para_pip_audit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.8.4")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    estado = next(item for item in diagnostico.herramientas if item.nombre == "pip-audit")
    assert estado.instalada is True
    assert estado.version_instalada == "2.7.3"


def test_doctor_reporta_interprete_y_red_para_proxy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.local:8080")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.8.4")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path)
    lineas = doctor.renderizar_reporte(diagnostico)
    assert any("Intérprete activo" in linea for linea in lineas)
    assert any("Python esperado .venv" in linea for linea in lineas)
    assert any("proxy configurado" in linea.lower() or "proxy detectado: sí" in linea.lower() for linea in lineas)
    assert "proxy" in diagnostico.diagnostico_red


def test_doctor_explica_wheelhouse_invalido_por_variable_entorno(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _escribir_lock_dev(tmp_path)
    wheelhouse_invalido = tmp_path / "wheelhouse.txt"
    wheelhouse_invalido.write_text("no-dir", encoding="utf-8")
    monkeypatch.setenv("CLINICDESK_WHEELHOUSE", str(wheelhouse_invalido))
    monkeypatch.setattr(doctor.metadata, "version", lambda nombre: "2.7.3" if nombre == "pip-audit" else "0.0.0")

    def fake_run(command, **_kwargs):
        if command[:5] == [sys.executable, "-m", "pip", "cache", "dir"]:
            return _Resultado(0, stdout="/tmp/pip-cache")
        if command[2] == "ruff":
            return _Resultado(0, stdout="ruff 0.8.4")
        if command[2] == "pytest":
            return _Resultado(0, stdout="pytest 8.3.2")
        if command[2] == "mypy":
            return _Resultado(0, stdout="mypy 1.13.0")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    diagnostico = doctor.diagnosticar_entorno_calidad(tmp_path, wheelhouse=wheelhouse_invalido)
    lineas = doctor.renderizar_reporte(diagnostico)
    assert "ruta inválida" in diagnostico.diagnostico_red
    assert any("Wheelhouse:" in linea and "ruta inválida" in linea for linea in lineas)

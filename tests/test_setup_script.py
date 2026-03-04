from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import setup


def test_setup_main_ejecuta_comandos_esperados(monkeypatch, tmp_path: Path) -> None:
    comandos: list[list[str]] = []
    venv_dir = tmp_path / ".venv"
    python_venv = venv_dir / "bin" / "python"
    original_exists = Path.exists

    def fake_run(command, **kwargs):
        comandos.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(setup, "PROJECT_ROOT", Path(__file__).resolve().parents[1])
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: python_venv)
    monkeypatch.setattr(Path, "exists", lambda self: True if self == python_venv else original_exists(self))

    rc = setup.main()

    assert rc == 0
    assert comandos[0] == [setup.sys.executable, "-m", "venv", str(venv_dir)]
    assert ["-m", "pip", "install", "-r", str(setup.PROJECT_ROOT / "requirements.txt")] == comandos[1][1:]
    assert ["-m", "pip", "install", "-r", str(setup.PROJECT_ROOT / "requirements-dev.txt")] == comandos[2][1:]
    assert comandos[3][1:] == ["-m", "ruff", "--version"]
    assert comandos[4][1:] == ["-m", "pytest", "--version"]
    assert comandos[5][1:] == ["-m", "pip_audit", "--version"]
    assert comandos[6][1:] == ["-m", "mypy", "--version"]


def test_setup_main_devuelve_error_si_falla_subproceso(monkeypatch, tmp_path: Path, capsys) -> None:
    venv_dir = tmp_path / ".venv"
    python_venv = venv_dir / "bin" / "python"
    original_exists = Path.exists

    def fake_run(command, **kwargs):
        if command[-1].endswith("requirements.txt"):
            return subprocess.CompletedProcess(command, 1)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(setup, "PROJECT_ROOT", Path(__file__).resolve().parents[1])
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: python_venv)
    monkeypatch.setattr(Path, "exists", lambda self: True if self == python_venv else original_exists(self))

    rc = setup.main()

    salida = capsys.readouterr().out
    assert rc == 1
    assert "[setup][error]" in salida
    assert "Instalar dependencias runtime" in salida


def test_instalar_dependencias_falla_si_falta_requirements(monkeypatch, tmp_path: Path) -> None:
    python_venv = tmp_path / "bin" / "python"
    original_exists = Path.exists

    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: False
        if self in {tmp_path / "requirements.txt", tmp_path / "requirements-dev.txt"}
        else original_exists(self),
    )

    try:
        setup._instalar_dependencias(python_venv)
    except RuntimeError as exc:
        assert "No se encontraron requirements.txt" in str(exc)
    else:
        raise AssertionError("Se esperaba RuntimeError cuando faltan requirements")

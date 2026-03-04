from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import setup


def test_setup_main_ejecuta_comandos_esperados(monkeypatch, tmp_path: Path) -> None:
    comandos: list[list[str]] = []
    venv_dir = tmp_path / ".venv"

    def fake_run(command, **kwargs):
        comandos.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: venv_dir / "bin" / "python")
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: self in {tmp_path / "requirements.txt", tmp_path / "requirements-dev.txt", venv_dir / "bin" / "python"},
    )

    rc = setup.main()

    assert rc == 0
    assert comandos[0] == [setup.sys.executable, "-m", "venv", str(venv_dir)]
    assert ["-m", "pip", "install", "-r", "requirements.txt"] == comandos[1][1:]
    assert ["-m", "pip", "install", "-r", "requirements-dev.txt"] == comandos[2][1:]
    assert comandos[3][1:] == ["-m", "ruff", "--version"]
    assert comandos[4][1:] == ["-m", "pytest", "--version"]
    assert comandos[5][1:] == ["-m", "pip_audit", "--version"]
    assert comandos[6][1:] == ["-m", "mypy", "--version"]


def test_setup_main_devuelve_error_si_falla_subproceso(monkeypatch, tmp_path: Path, capsys) -> None:
    venv_dir = tmp_path / ".venv"

    def fake_run(command, **kwargs):
        if command[-1] == "requirements.txt":
            return subprocess.CompletedProcess(command, 1)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: venv_dir / "bin" / "python")
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: self
        in {venv_dir, tmp_path / "requirements.txt", tmp_path / "requirements-dev.txt", venv_dir / "bin" / "python"},
    )

    rc = setup.main()

    salida = capsys.readouterr().out
    assert rc == 1
    assert "[setup][error]" in salida
    assert "Instalar dependencias runtime" in salida

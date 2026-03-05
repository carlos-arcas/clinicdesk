from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from scripts import run_demo


class SubprocessSpy:
    def __init__(self, returncodes: list[int]) -> None:
        self._returncodes = returncodes
        self.calls: list[dict[str, object]] = []

    def __call__(self, command, cwd=None, env=None, check=False):
        index = len(self.calls)
        self.calls.append({"command": command, "cwd": cwd, "env": env, "check": check})
        returncode = self._returncodes[index]
        return SimpleNamespace(returncode=returncode)


def _configurar_entorno(monkeypatch, tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(run_demo, "_resolver_repo_root", lambda: repo_root)
    monkeypatch.setattr(run_demo.os, "chdir", lambda _: None)
    return repo_root


def test_run_demo_default_siembra_y_arranca(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([0, 0])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main([])

    assert result == 0
    assert len(spy.calls) == 2
    seed_call = spy.calls[0]
    app_call = spy.calls[1]
    db_demo = str((repo_root / run_demo.RUTA_DB_DEMO).resolve())
    assert seed_call["command"] == [
        os.sys.executable,
        "seed_demo_data.py",
        "--sqlite-path",
        db_demo,
        "--reset",
    ]
    assert app_call["command"] == [os.sys.executable, "-m", run_demo.NOMBRE_MODULO_APP]


def test_run_demo_skip_seed_ejecuta_solo_app(monkeypatch, tmp_path: Path) -> None:
    _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([0])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main(["--skip-seed"])

    assert result == 0
    assert len(spy.calls) == 1
    assert spy.calls[0]["command"] == [os.sys.executable, "-m", run_demo.NOMBRE_MODULO_APP]


def test_run_demo_seed_falla_y_no_arranca_app(monkeypatch, tmp_path: Path) -> None:
    _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([7])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main([])

    assert result == 7
    assert len(spy.calls) == 1


def test_run_demo_respeta_db_path_explicito_en_entorno(monkeypatch, tmp_path: Path) -> None:
    _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([0, 0])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)
    monkeypatch.setenv("CLINICDESK_DB_PATH", "/tmp/db_personalizada.db")

    result = run_demo.main([])

    assert result == 0
    seed_command = spy.calls[0]["command"]
    assert "--sqlite-path" in seed_command
    assert "/tmp/db_personalizada.db" in seed_command


def test_run_demo_env_incluye_db_demo_y_no_pisa_pythonpath(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([0, 0])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)
    monkeypatch.setenv("PYTHONPATH", "src")

    result = run_demo.main([])

    assert result == 0
    db_demo = str((repo_root / run_demo.RUTA_DB_DEMO).resolve())
    env_seed = spy.calls[0]["env"]
    assert env_seed["CLINICDESK_DB_PATH"] == db_demo
    assert env_seed["PYTHONPATH"] == "src"

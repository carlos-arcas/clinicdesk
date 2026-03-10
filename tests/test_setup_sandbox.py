from __future__ import annotations

from types import SimpleNamespace

from scripts import setup_sandbox


def test_instalacion_dev_con_wheelhouse(monkeypatch, tmp_path):
    monkeypatch.setattr(setup_sandbox, "RAIZ_REPO", tmp_path)
    monkeypatch.setenv("CLINICDESK_WHEELHOUSE", str(tmp_path / "wh"))
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.0.0\n", encoding="utf-8")
    wheelhouse = tmp_path / "wh"
    wheelhouse.mkdir()
    (wheelhouse / "pytest-8.0.0-py3-none-any.whl").write_text("x", encoding="utf-8")
    comandos = []

    def _run_mock(comando, **_kwargs):
        comandos.append(comando)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(setup_sandbox.subprocess, "run", _run_mock)

    assert setup_sandbox._instalar_archivo_requirements("requirements-dev.txt") is True
    assert comandos, "Se esperaba una invocación a pip"
    assert "--no-index" in comandos[0]
    assert "--find-links" in comandos[0]
    assert str(wheelhouse) in comandos[0]


def test_instalacion_dev_sin_wheelhouse(monkeypatch, tmp_path):
    monkeypatch.setattr(setup_sandbox, "RAIZ_REPO", tmp_path)
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.0.0\n", encoding="utf-8")
    comandos = []

    def _run_mock(comando, **_kwargs):
        comandos.append(comando)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(setup_sandbox.subprocess, "run", _run_mock)

    assert setup_sandbox._instalar_archivo_requirements("requirements-dev.txt") is True
    assert comandos, "Se esperaba una invocación a pip"
    assert "--no-index" not in comandos[0]
    assert "--find-links" not in comandos[0]


def test_instalacion_falla_por_red_muestra_mensaje_accionable(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(setup_sandbox, "RAIZ_REPO", tmp_path)
    monkeypatch.setenv("CLINICDESK_WHEELHOUSE", str(tmp_path / "sin_wheelhouse"))
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.0.0\n", encoding="utf-8")

    def _run_mock(_comando, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="ProxyError: 407 Proxy Authentication Required")

    monkeypatch.setattr(setup_sandbox.subprocess, "run", _run_mock)

    assert setup_sandbox._instalar_archivo_requirements("requirements-dev.txt") is False
    salida = capsys.readouterr().out
    assert "red/proxy" in salida
    assert "build_wheelhouse" in salida

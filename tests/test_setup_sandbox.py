from __future__ import annotations

from types import SimpleNamespace

from scripts import setup_sandbox


def test_instalacion_dev_con_wheelhouse(monkeypatch, tmp_path):
    monkeypatch.setattr(setup_sandbox, "RAIZ_REPO", tmp_path)
    (tmp_path / "requirements-dev.txt").write_text("pytest==8.0.0\n", encoding="utf-8")
    (tmp_path / "wheelhouse").mkdir()
    comandos = []

    def _run_mock(comando, **_kwargs):
        comandos.append(comando)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(setup_sandbox.subprocess, "run", _run_mock)

    assert setup_sandbox._instalar_archivo_requirements("requirements-dev.txt") is True
    assert comandos, "Se esperaba una invocación a pip"
    assert "--no-index" in comandos[0]
    assert "--find-links" in comandos[0]
    assert "wheelhouse" in comandos[0]


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

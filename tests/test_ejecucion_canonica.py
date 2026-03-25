from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality_gate_components import ejecucion_canonica


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text('[tool.mypy]\npython_version = "3.11"\n', encoding='utf-8')
    return tmp_path


def test_resolver_ejecucion_canonica_reejecuta_con_venv_repo(monkeypatch: pytest.MonkeyPatch, repo_root: Path) -> None:
    python_venv = repo_root / ".venv" / "bin" / "python"
    python_venv.parent.mkdir(parents=True)
    python_venv.write_text("", encoding="utf-8")
    python_venv.chmod(0o755)
    monkeypatch.setattr(ejecucion_canonica.sys, "executable", "/usr/bin/python3")
    monkeypatch.delenv(ejecucion_canonica.MARCADOR_REEJECUCION, raising=False)
    monkeypatch.delenv("CI", raising=False)

    decision = ejecucion_canonica.resolver_ejecucion_canonica(repo_root, exigir_venv_repo=True)

    assert decision.accion == "reejecutar"
    assert decision.python_objetivo == python_venv


def test_reason_codes_operativos_canonico_registrados() -> None:
    assert ejecucion_canonica.REASON_CODES_OPERATIVOS_CANONICO == ("VENV_REPO_NO_DISPONIBLE",)


def test_resolver_ejecucion_canonica_bloquea_si_falta_venv(monkeypatch: pytest.MonkeyPatch, repo_root: Path) -> None:
    monkeypatch.setattr(ejecucion_canonica.sys, "executable", "/usr/bin/python3")
    monkeypatch.delenv("CI", raising=False)

    decision = ejecucion_canonica.resolver_ejecucion_canonica(repo_root, exigir_venv_repo=True)

    assert decision.accion == "bloquear"
    assert any("VENV_REPO_NO_DISPONIBLE" in linea for linea in decision.mensaje)
    assert any("todavía no se validó funcionalmente" in linea for linea in decision.mensaje)
    assert any("python scripts/setup.py" in linea for linea in decision.mensaje)
    assert any("red/proxy/wheelhouse" in linea for linea in decision.mensaje)


def test_resolver_ejecucion_canonica_bloquea_si_python_repo_no_es_ejecutable(
    monkeypatch: pytest.MonkeyPatch, repo_root: Path
) -> None:
    python_venv = repo_root / ".venv" / "bin" / "python"
    python_venv.parent.mkdir(parents=True)
    python_venv.write_text("", encoding="utf-8")
    python_venv.chmod(0o644)
    monkeypatch.setattr(ejecucion_canonica.sys, "executable", "/usr/bin/python3")
    monkeypatch.delenv("CI", raising=False)

    decision = ejecucion_canonica.resolver_ejecucion_canonica(repo_root, exigir_venv_repo=True)

    assert decision.accion == "bloquear"
    assert any(str(python_venv) in linea for linea in decision.mensaje)


def test_resolver_ejecucion_canonica_no_afecta_ci(monkeypatch: pytest.MonkeyPatch, repo_root: Path) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(ejecucion_canonica.sys, "executable", "/opt/hostedtoolcache/Python/3.11.9/x64/bin/python")

    decision = ejecucion_canonica.resolver_ejecucion_canonica(repo_root, exigir_venv_repo=True)

    assert decision.accion == "continuar"


def test_reejecutar_en_python_objetivo_propagando_entorno(monkeypatch: pytest.MonkeyPatch, repo_root: Path) -> None:
    python_venv = repo_root / ".venv" / "bin" / "python"
    decision = ejecucion_canonica.DecisionEjecucionCanonica("reejecutar", python_objetivo=python_venv)
    observado: dict[str, object] = {}

    def fake_run(comando, **kwargs):
        observado["comando"] = comando
        observado["env"] = kwargs["env"]
        return type("Proceso", (), {"returncode": 7})()

    monkeypatch.setattr(ejecucion_canonica.subprocess, "run", fake_run)

    rc = ejecucion_canonica.reejecutar_en_python_objetivo(
        decision,
        ["-m", "scripts.gate_pr"],
        env_extra={"CLINICDESK_SANDBOX_MODE": "1"},
    )

    assert rc == 7
    assert observado["comando"] == [str(python_venv), "-m", "scripts.gate_pr"]
    assert observado["env"][ejecucion_canonica.MARCADOR_REEJECUCION] == "1"
    assert observado["env"]["CLINICDESK_SANDBOX_MODE"] == "1"

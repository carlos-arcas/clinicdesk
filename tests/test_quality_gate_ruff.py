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
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
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
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    comandos: list[list[str]] = []

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        return _Resultado(returncode=2, stderr="fallo")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 2
    assert comandos == [[sys.executable, "-m", "ruff", "--version"]]


def test_genera_diff_y_artefacto_si_format_check_falla(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
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
            return _Resultado(returncode=1, stdout="--- diff ---", stderr="")
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
    assert "returncode: 1" in artefacto


def test_imprime_diff_en_logs_con_delimitadores(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=0, stdout="linea diff", stderr="")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("INFO"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    texto = caplog.text
    assert ruff_checks.DELIMITADOR_INICIO_DIFF in texto
    assert "linea diff" in texto
    assert ruff_checks.DELIMITADOR_FIN_DIFF in texto


def test_diff_con_returncode_uno_no_loguea_error_falso(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=1, stdout="diff valido", stderr="")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("INFO"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert "ruff_format_diff_fallo" not in caplog.text
    assert "ruff_format_diff_ok" in caplog.text


def test_diff_loguea_error_cuando_falla_realmente(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=2, stdout="", stderr="fallo de ejecucion")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert "ruff_format_diff_fallo" in caplog.text


def test_trunca_diff_largo_de_forma_estable() -> None:
    lineas = [f"linea {indice}" for indice in range(1, 301)]
    contenido = "\n".join(lineas)

    resultado = ruff_checks._construir_diff_para_logs(contenido)

    assert "linea 1" in resultado
    assert "linea 200" in resultado
    assert "linea 201" not in resultado
    assert "linea 251" in resultado
    assert "linea 250" not in resultado
    assert "diff truncado: 50 líneas omitidas" in resultado


def test_persistencia_estable_si_diff_falla(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
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
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
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


def test_loguea_fallo_real_de_format_check(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py"])

    def fake_run(command, **kwargs):
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            return _Resultado(returncode=1)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=0, stdout="ok", stderr="")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert "ruff_format_check_fallo" in caplog.text


def test_falla_si_ruff_no_coincide_con_pin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\n", encoding="utf-8")
    comandos: list[list[str]] = []

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        return _Resultado(returncode=0, stdout="ruff 0.14.11")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 1
    assert comandos == [[sys.executable, "-m", "ruff", "--version"]]


def test_extrae_pin_ruff_con_espacios_y_comentario() -> None:
    assert ruff_checks._extraer_version_ruff_pinneada_desde_linea("ruff == 0.8.4   # pin-ci") == "0.8.4"


def test_log_de_desalineacion_indica_comando_de_instalacion(
    monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.8.4\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        return _Resultado(returncode=0, stdout="ruff 0.14.11")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert "python -m pip install -r requirements-dev.txt" in caplog.text

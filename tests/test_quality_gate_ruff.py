from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts import _ruff_targets
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


def test_run_required_ruff_checks_lotea_comandos_largos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    targets = [f"clinicdesk/modulo_{indice}_{'a' * 40}.py" for indice in range(6)]
    comandos: list[list[str]] = []

    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: targets)
    monkeypatch.setattr(_ruff_targets, "LIMITE_COMANDO_RUFF_CHARS", 170)

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        return _Resultado(returncode=0)

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    assert ruff_checks.run_required_ruff_checks(tmp_path) == 0

    comandos_check = [comando for comando in comandos if comando[3] == "check"]
    comandos_format = [comando for comando in comandos if comando[3:5] == ["format", "--check"]]
    assert len(comandos_check) > 1
    assert len(comandos_format) == len(comandos_check)
    assert [ruta for comando in comandos_check for ruta in comando[4:]] == targets
    assert all(
        len(subprocess.list2cmdline(comando)) <= _ruff_targets.LIMITE_COMANDO_RUFF_CHARS
        for comando in [*comandos_check, *comandos_format]
    )


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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py\n1 file would be reformatted")
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=1, stdout="--- diff scripts/a.py ---", stderr="")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert comandos[-1] == [sys.executable, "-m", "ruff", "format", "--diff", "scripts/a.py"]
    artefacto = (tmp_path / "docs" / "ruff_format_diff.txt").read_text(encoding="utf-8")
    assert "--- diff scripts/a.py ---" in artefacto
    assert "returncode: 1" in artefacto


def test_ejecuta_diff_con_multiples_archivos_parseados(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: ["scripts/a.py", "scripts/b.py"])
    comandos: list[list[str]] = []

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            salida = "\n".join(["Would reformat: scripts/a.py", "Would reformat: scripts/b.py"])
            return _Resultado(returncode=1, stdout=salida)
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=1, stdout="--- diff multiple ---")
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
        "scripts/a.py",
        "scripts/b.py",
    ]


def test_fallback_si_no_hay_archivos_parseables(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path: Path) -> None:
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
            return _Resultado(returncode=1, stdout="contenido no parseable")
        raise AssertionError(f"No debe ejecutar diff sin targets reales: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    with caplog.at_level("WARNING"):
        rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    assert all(cmd[3:5] != ["format", "--diff"] for cmd in comandos)
    artefacto = (tmp_path / "docs" / "ruff_format_diff.txt").read_text(encoding="utf-8")
    assert "sin archivos parseables" in artefacto
    assert "contenido no parseable" in artefacto
    assert "ruff_format_diff_sin_targets_parseables" in caplog.text


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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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
            return _Resultado(returncode=1, stdout="Would reformat: scripts/a.py")
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

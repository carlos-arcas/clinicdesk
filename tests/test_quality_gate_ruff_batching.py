from __future__ import annotations

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


def test_run_required_ruff_checks_acota_format_check_a_diez_archivos_por_lote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("ruff==0.12.0\n", encoding="utf-8")
    targets = [f"clinicdesk/modulo_{indice}.py" for indice in range(14)]
    comandos: list[list[str]] = []

    monkeypatch.setattr(ruff_checks, "obtener_targets_python", lambda _: targets)
    monkeypatch.setattr(_ruff_targets, "LIMITE_COMANDO_RUFF_CHARS", 1000)

    def fake_run(command, **kwargs):
        comandos.append(list(command))
        if command[:4] == [sys.executable, "-m", "ruff", "--version"]:
            return _Resultado(returncode=0, stdout="ruff 0.12.0")
        if command[3] == "check":
            return _Resultado(returncode=0)
        if command[3:5] == ["format", "--check"]:
            rutas_lote = command[5:]
            if rutas_lote == targets[:10]:
                salida = "\n".join(f"Would reformat: {ruta}" for ruta in rutas_lote)
                return _Resultado(returncode=1, stdout=salida)
            raise AssertionError(f"No debe alcanzar un segundo lote tras el primer fallo: {command}")
        if command[3:5] == ["format", "--diff"]:
            return _Resultado(returncode=1, stdout="--- diff first batch ---")
        raise AssertionError(f"Comando inesperado: {command}")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    rc = ruff_checks.run_required_ruff_checks(tmp_path)

    assert rc == 1
    comandos_check = [comando for comando in comandos if comando[3] == "check"]
    comandos_format = [comando for comando in comandos if comando[3:5] == ["format", "--check"]]
    assert comandos_check == [[sys.executable, "-m", "ruff", "check", *targets]]
    assert comandos_format == [[sys.executable, "-m", "ruff", "format", "--check", *targets[:10]]]
    assert comandos[-1] == [sys.executable, "-m", "ruff", "format", "--diff", *targets[:10]]

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import _ruff_targets


@pytest.mark.parametrize(
    "salida_git,esperado",
    [
        (
            "README.md\n.github/workflows/ci.yml\nconfig/settings.yaml\nscripts/gate_pr.py\ntests/test_algo.py\n",
            ["scripts/gate_pr.py", "tests/test_algo.py"],
        ),
        ("README.md\ndocs/guia.yml\n", ["."]),
    ],
)
def test_obtener_targets_python_prioriza_archivos_python(
    monkeypatch: pytest.MonkeyPatch, salida_git: str, esperado: list[str]
) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=salida_git, stderr="")

    monkeypatch.setattr(_ruff_targets.subprocess, "run", fake_run)

    assert _ruff_targets.obtener_targets_python(Path("/repo")) == esperado


def test_obtener_targets_python_fallback_si_git_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="fatal")

    monkeypatch.setattr(_ruff_targets.subprocess, "run", fake_run)

    assert _ruff_targets.obtener_targets_python(Path("/repo")) == ["."]

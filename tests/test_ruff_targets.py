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


def test_agrupar_targets_para_comando_respeta_limite() -> None:
    comando_base = ["python", "-m", "ruff", "check"]
    targets = [f"tests/{'a' * 18}_{indice}.py" for indice in range(4)]

    lotes = _ruff_targets.agrupar_targets_para_comando(comando_base, targets, limite_chars=70)

    assert [target for lote in lotes for target in lote] == targets
    assert len(lotes) == 4
    assert all(len(subprocess.list2cmdline([*comando_base, *lote])) <= 70 for lote in lotes)


def test_agrupar_targets_para_comando_respeta_maximo_de_targets() -> None:
    comando_base = ["python", "-m", "ruff", "format", "--check"]
    targets = [f"tests/test_{indice}.py" for indice in range(7)]

    lotes = _ruff_targets.agrupar_targets_para_comando(
        comando_base, targets, limite_chars=1000, max_targets_por_lote=3
    )

    assert [target for lote in lotes for target in lote] == targets
    assert [len(lote) for lote in lotes] == [3, 3, 1]

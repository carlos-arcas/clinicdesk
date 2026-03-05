from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.quality_gate_components import ruff_checks


def test_resolve_python_targets_excluye_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command, **kwargs):
        salida = "scripts/gate_pr.py\n.github/workflows/ci.yml\ndocs/config.yaml\ntests/test_algo.py\n"
        return subprocess.CompletedProcess(command, 0, stdout=salida)

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    targets = ruff_checks._resolve_python_targets(Path("/repo"))

    assert targets == ["scripts/gate_pr.py", "tests/test_algo.py"]


def test_resolve_python_targets_fallback_si_git_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="error")

    monkeypatch.setattr(ruff_checks.subprocess, "run", fake_run)

    targets = ruff_checks._resolve_python_targets(Path("/repo"))

    assert targets == ["."]

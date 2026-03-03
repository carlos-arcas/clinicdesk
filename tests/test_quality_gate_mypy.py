from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import quality_gate


def test_run_mypy_blocking_scope_uses_scope_file(tmp_path: Path, monkeypatch) -> None:
    scope_path = tmp_path / "mypy_scope.txt"
    scope_path.write_text("clinicdesk/app/domain/enums.py\n", encoding="utf-8")

    observed_commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        observed_commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(quality_gate, "MYPY_SCOPE_PATH", scope_path)
    monkeypatch.setattr(quality_gate.subprocess, "run", fake_run)

    rc = quality_gate._run_mypy_blocking_scope()

    assert rc == 0
    assert observed_commands
    assert observed_commands[0][:3] == [quality_gate.sys.executable, "-m", "mypy"]
    assert observed_commands[0][3:] == ["clinicdesk/app/domain/enums.py"]


def test_run_mypy_report_generates_artifact_even_with_errors(tmp_path: Path, monkeypatch) -> None:
    report_path = tmp_path / "mypy_report.txt"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout="clinicdesk/app/foo.py:10: error: tipo invalido [arg-type]",
            stderr="",
        )

    monkeypatch.setattr(quality_gate, "MYPY_REPORT_PATH", report_path)
    monkeypatch.setattr(quality_gate.subprocess, "run", fake_run)

    rc = quality_gate._run_mypy_report()

    assert rc == 0
    contenido = report_path.read_text(encoding="utf-8")
    assert "Exit code: 1" in contenido
    assert "error: tipo invalido" in contenido

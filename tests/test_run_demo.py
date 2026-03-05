from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import run_demo


class SubprocessSpy:
    def __init__(self, resultados: list[dict[str, object]], error_en_llamada: int | None = None) -> None:
        self._resultados = resultados
        self._error_en_llamada = error_en_llamada
        self.calls: list[dict[str, object]] = []

    def __call__(self, command, cwd=None, env=None, check=False, capture_output=False, text=False):
        index = len(self.calls)
        self.calls.append(
            {
                "command": command,
                "cwd": cwd,
                "env": env,
                "check": check,
                "capture_output": capture_output,
                "text": text,
            }
        )
        if self._error_en_llamada is not None and index == self._error_en_llamada:
            raise OSError("fallo operativo")
        resultado = self._resultados[index]
        return subprocess.CompletedProcess(
            args=command,
            returncode=int(resultado["returncode"]),
            stdout=str(resultado.get("stdout", "")),
            stderr=str(resultado.get("stderr", "")),
        )


def _configurar_entorno(monkeypatch, tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(run_demo, "_resolver_repo_root", lambda: repo_root)
    monkeypatch.setattr(run_demo.os, "chdir", lambda _: None)
    monkeypatch.setattr(run_demo.platform, "platform", lambda: "test-platform")
    return repo_root


def _leer_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_run_demo_seed_falla_genera_diagnostico_y_no_arranca_app(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy([{"returncode": 7, "stdout": "ok seed", "stderr": "error seed"}])
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main([])

    assert result == 7
    assert len(spy.calls) == 1
    logs_dir = repo_root / "logs"
    assert (logs_dir / "demo_seed_stdout.log").read_text(encoding="utf-8") == "ok seed"
    assert (logs_dir / "demo_seed_stderr.log").read_text(encoding="utf-8") == "error seed"
    assert (logs_dir / "demo_app_stdout.log").read_text(encoding="utf-8") == ""
    summary = _leer_json(logs_dir / "demo_failure_summary.json")
    assert summary["reason_code"] == "seed_failed"
    assert summary["returncodes"] == {"seed": 7, "app": None}


def test_run_demo_app_falla_genera_summary_con_reason_code(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy(
        [
            {"returncode": 0, "stdout": "seed listo", "stderr": ""},
            {"returncode": 3, "stdout": "app stdout", "stderr": "app error"},
        ]
    )
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main([])

    assert result == 3
    logs_dir = repo_root / "logs"
    assert (logs_dir / "demo_seed_stdout.log").read_text(encoding="utf-8") == "seed listo"
    assert (logs_dir / "demo_app_stderr.log").read_text(encoding="utf-8") == "app error"
    summary = _leer_json(logs_dir / "demo_failure_summary.json")
    assert summary["reason_code"] == "app_failed"
    assert summary["returncodes"] == {"seed": 0, "app": 3}


def test_run_demo_exito_sobrescribe_logs_y_no_deja_summary(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    logs_dir = repo_root / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "demo_failure_summary.json").write_text("{}", encoding="utf-8")
    spy = SubprocessSpy(
        [
            {"returncode": 0, "stdout": "seed nuevo", "stderr": ""},
            {"returncode": 0, "stdout": "app nuevo", "stderr": ""},
        ]
    )
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    result = run_demo.main([])

    assert result == 0
    assert not (logs_dir / "demo_failure_summary.json").exists()
    assert (logs_dir / "demo_seed_stdout.log").read_text(encoding="utf-8") == "seed nuevo"
    assert (logs_dir / "demo_app_stdout.log").read_text(encoding="utf-8") == "app nuevo"


def test_run_demo_summary_redacta_pii_y_tokens(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    stderr_seed = "correo user@mail.com telefono +34 600 123 123 dni 12345678Z token sk_test_abc"
    stderr_app = "public pk_live_999 y otro correo admin@clinic.com"
    spy = SubprocessSpy(
        [
            {"returncode": 0, "stdout": "", "stderr": stderr_seed},
            {"returncode": 4, "stdout": "", "stderr": stderr_app},
        ]
    )
    monkeypatch.setattr(run_demo.subprocess, "run", spy)

    run_demo.main([])

    summary = _leer_json(repo_root / "logs" / "demo_failure_summary.json")
    seed_line = summary["stderr_lineas"]["seed"][0]
    app_line = summary["stderr_lineas"]["app"][0]
    assert "[REDACTED]" in seed_line
    assert "[REDACTED]" in app_line
    assert "user@mail.com" not in seed_line
    assert "12345678Z" not in seed_line
    assert "sk_test_abc" not in seed_line
    assert "pk_live_999" not in app_line


def test_run_demo_env_incluye_db_demo_y_no_pisa_pythonpath(monkeypatch, tmp_path: Path) -> None:
    repo_root = _configurar_entorno(monkeypatch, tmp_path)
    spy = SubprocessSpy(
        [
            {"returncode": 0, "stdout": "", "stderr": ""},
            {"returncode": 0, "stdout": "", "stderr": ""},
        ]
    )
    monkeypatch.setattr(run_demo.subprocess, "run", spy)
    monkeypatch.setenv("PYTHONPATH", "src")

    result = run_demo.main([])

    assert result == 0
    db_demo = str((repo_root / run_demo.RUTA_DB_DEMO).resolve())
    env_seed = spy.calls[0]["env"]
    assert env_seed["CLINICDESK_DB_PATH"] == db_demo
    assert env_seed["PYTHONPATH"] == "src"
    assert spy.calls[0]["capture_output"] is True
    assert spy.calls[0]["text"] is True

from __future__ import annotations

from scripts import gate_rapido


class _ProcesoFalso:
    def __init__(self, returncode: int):
        self.returncode = returncode


def test_main_invoca_entrypoint_report_only(monkeypatch):
    observado: dict[str, object] = {}

    def fake_chdir(path):
        observado["cwd"] = path

    def fake_run(cmd, check, env):
        observado["cmd"] = list(cmd)
        observado["check"] = check
        observado["env"] = dict(env)
        return _ProcesoFalso(returncode=0)

    monkeypatch.delenv("CLINICDESK_SANDBOX_MODE", raising=False)
    monkeypatch.setattr(gate_rapido.os, "chdir", fake_chdir)
    monkeypatch.setattr(gate_rapido.subprocess, "run", fake_run)

    rc = gate_rapido.main()

    assert rc == 0
    assert observado["cwd"] == gate_rapido.REPO_ROOT
    assert observado["cmd"] == [
        gate_rapido.sys.executable,
        "-m",
        "scripts.quality_gate_components.entrypoint",
        "--report-only",
    ]
    assert observado["check"] is False


def test_main_inyecta_sandbox_mode_si_no_existe(monkeypatch):
    observado: dict[str, object] = {}

    def fake_run(cmd, check, env):
        observado["env"] = dict(env)
        return _ProcesoFalso(returncode=3)

    monkeypatch.delenv("CLINICDESK_SANDBOX_MODE", raising=False)
    monkeypatch.setattr(gate_rapido.os, "chdir", lambda *_: None)
    monkeypatch.setattr(gate_rapido.subprocess, "run", fake_run)

    rc = gate_rapido.main()

    assert rc == 3
    assert observado["env"]["CLINICDESK_SANDBOX_MODE"] == "1"


def test_main_respeta_sandbox_mode_preexistente(monkeypatch):
    observado: dict[str, object] = {}

    def fake_run(cmd, check, env):
        observado["env"] = dict(env)
        return _ProcesoFalso(returncode=0)

    monkeypatch.setenv("CLINICDESK_SANDBOX_MODE", "0")
    monkeypatch.setattr(gate_rapido.os, "chdir", lambda *_: None)
    monkeypatch.setattr(gate_rapido.subprocess, "run", fake_run)

    rc = gate_rapido.main()

    assert rc == 0
    assert observado["env"]["CLINICDESK_SANDBOX_MODE"] == "0"


def test_main_propaga_returncode(monkeypatch):
    monkeypatch.setattr(gate_rapido.os, "chdir", lambda *_: None)
    monkeypatch.setattr(
        gate_rapido.subprocess,
        "run",
        lambda *args, **kwargs: _ProcesoFalso(returncode=11),
    )

    assert gate_rapido.main() == 11

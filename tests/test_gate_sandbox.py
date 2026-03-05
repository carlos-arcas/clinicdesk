from __future__ import annotations

from scripts import gate_sandbox


class _ProcesoFalso:
    def __init__(self, returncode: int):
        self.returncode = returncode


def test_main_ejecuta_gate_pr_con_sandbox_mode_por_defecto(monkeypatch):
    observado: dict[str, object] = {}

    def fake_chdir(path):
        observado["cwd"] = path

    def fake_run(cmd, check, env):
        observado["cmd"] = list(cmd)
        observado["check"] = check
        observado["env"] = dict(env)
        return _ProcesoFalso(returncode=7)

    monkeypatch.delenv("CLINICDESK_SANDBOX_MODE", raising=False)
    monkeypatch.setattr(gate_sandbox.os, "chdir", fake_chdir)
    monkeypatch.setattr(gate_sandbox.subprocess, "run", fake_run)

    rc = gate_sandbox.main()

    assert rc == 7
    assert observado["cwd"] == gate_sandbox.REPO_ROOT
    assert observado["cmd"] == [gate_sandbox.sys.executable, "-m", "scripts.gate_pr"]
    assert observado["check"] is False
    env = observado["env"]
    assert env["CLINICDESK_SANDBOX_MODE"] == "1"


def test_main_respeta_valores_previos_de_entorno(monkeypatch):
    observado: dict[str, object] = {}

    def fake_run(cmd, check, env):
        observado["env"] = dict(env)
        return _ProcesoFalso(returncode=0)

    monkeypatch.setenv("CLINICDESK_SANDBOX_MODE", "0")
    monkeypatch.setattr(gate_sandbox.os, "chdir", lambda *_: None)
    monkeypatch.setattr(gate_sandbox.subprocess, "run", fake_run)

    rc = gate_sandbox.main()

    assert rc == 0
    env = observado["env"]
    assert env["CLINICDESK_SANDBOX_MODE"] == "0"
